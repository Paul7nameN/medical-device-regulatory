from datetime import datetime
from typing import List, Optional, Dict, Any
import base64
import logging

from app.ai.client import (
    ModelArkClient,
    ImageFormat,
    ChartViolationType,
    AIError,
    AIValidationError,
    AIImageError
)
from app.ai.image.models import (
    ChartAnalysisResult,
    ChartViolation,
    TemperatureReading
)
from app.ai.image.prompts import (
    SYSTEM_PROMPT_CHART_ANALYSIS,
    IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE
)
from app.config import settings

logger = logging.getLogger(__name__)


class ChartAnalyzer:
    def __init__(self, client: Optional[ModelArkClient] = None):
        self.client = client or ModelArkClient()
    
    async def analyze(
        self,
        image_bytes: bytes,
        image_format: ImageFormat = ImageFormat.PNG
    ) -> ChartAnalysisResult:
        if not settings.ai_enabled:
            raise AIValidationError(
                "AI analysis is not enabled. Set MODELARK_API_KEY environment variable."
            )
        
        start_time = datetime.now()
        
        if not self.client.validate_image_size(image_bytes):
            raise AIImageError("Image exceeds maximum size of 10MB")
        
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        response = await self.client.analyze_image(
            image_base64=image_base64,
            prompt=f"{SYSTEM_PROMPT_CHART_ANALYSIS}\n\n{IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE}",
            image_format=image_format
        )
        
        content = self._extract_response_content(response)
        parsed = ModelArkClient.parse_json_response(content)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return self._build_result(parsed, response, duration)
    
    def _extract_response_content(self, response: Dict[str, Any]) -> str:
        try:
            choices = response.get('choices', [])
            if not choices:
                return '{}'
            
            message = choices[0].get('message', {})
            content = message.get('content', '{}')
            
            return content
        except (KeyError, IndexError, TypeError):
            return '{}'
    
    def _extract_data_points(self, parsed: Dict[str, Any]) -> List[TemperatureReading]:
        data_points = []
        
        possible_fields = [
            "data_points",
            "time_series",
            "readings",
            "temperature_data",
            "chart_data",
            "readings"
        ]
        
        data_array = None
        for field in possible_fields:
            if field in parsed and isinstance(parsed[field], list):
                data_array = parsed[field]
                logger.info(f"Found data points in field: {field}")
                break
        
        if data_array is None:
            logger.warning("No data_points or time_series field found in VLLM response")
            return []
        
        for item in data_array:
            if not isinstance(item, dict):
                continue
            
            try:
                reading = self._parse_temperature_reading(item)
                if reading:
                    data_points.append(reading)
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Failed to parse temperature reading: {e}")
                continue
        
        logger.info(f"Extracted {len(data_points)} temperature readings from VLLM response")
        return data_points
    
    def _parse_temperature_reading(self, item: Dict[str, Any]) -> Optional[TemperatureReading]:
        time_str = item.get("time")
        
        if not time_str:
            hour = item.get("hour")
            minute = item.get("minute", 0)
            if hour is not None:
                time_str = f"{int(hour):02d}:{int(minute):02d}"
        
        if not time_str:
            return None
        
        sensor_a = None
        possible_a_fields = ["sensor_a", "sensorA", "temperature", "temp", "value", "temp_a"]
        for field in possible_a_fields:
            val = item.get(field)
            if val is not None and isinstance(val, (int, float)):
                sensor_a = float(val)
                break
        
        if sensor_a is None:
            return None
        
        sensor_b = None
        possible_b_fields = ["sensor_b", "sensorB", "temp_b"]
        for field in possible_b_fields:
            val = item.get(field)
            if val is not None and isinstance(val, (int, float)):
                sensor_b = float(val)
                break
        
        timestamp = None
        timestamp_str = item.get("timestamp")
        if timestamp_str:
            timestamp = ModelArkClient.safe_parse_datetime(timestamp_str)
        
        source = item.get("source", "chart_image")
        
        return TemperatureReading(
            time=str(time_str),
            timestamp=timestamp,
            sensor_a=sensor_a,
            sensor_b=sensor_b,
            source=str(source)
        )
    
    def _generate_fallback_points(
        self,
        parsed: Dict[str, Any]
    ) -> List[TemperatureReading]:
        time_range = parsed.get("time_range", {}) or {}
        temp_range = parsed.get("temperature_range", {}) or {}
        
        start_time = ModelArkClient.safe_parse_datetime(
            time_range.get("start") if isinstance(time_range, dict) else None
        )
        end_time = ModelArkClient.safe_parse_datetime(
            time_range.get("end") if isinstance(time_range, dict) else None
        )
        
        temp_min = temp_range.get("min") if isinstance(temp_range, dict) else None
        temp_max = temp_range.get("max") if isinstance(temp_range, dict) else None
        
        avg_temp = 5.0
        if temp_min is not None and temp_max is not None:
            avg_temp = (float(temp_min) + float(temp_max)) / 2
        
        if start_time and end_time:
            hours_diff = (end_time - start_time).total_seconds() / 3600
            
            num_points = max(2, min(int(hours_diff) + 1, 12))
            points = []
            
            for i in range(num_points):
                ratio = i / (num_points - 1) if num_points > 1 else 0
                point_time = start_time + (end_time - start_time) * ratio
                
                points.append(TemperatureReading(
                    time=point_time.strftime("%H:%M"),
                    timestamp=point_time,
                    sensor_a=round(avg_temp + (ratio - 0.5) * 0.2, 1),
                    source="chart_image_fallback"
                ))
            
            logger.info(f"Generated {len(points)} fallback points from time_range")
            return points
        
        return []
    
    def _build_result(
        self,
        parsed: Dict[str, Any],
        raw_response: Dict[str, Any],
        duration: float
    ) -> ChartAnalysisResult:
        violations = []
        violation_dicts = parsed.get("violations", [])
        
        if isinstance(violation_dicts, list):
            for v in violation_dicts:
                if not isinstance(v, dict):
                    continue
                try:
                    violation_type_str = v.get("violation_type")
                    violation_type = None
                    if violation_type_str:
                        try:
                            violation_type = ChartViolationType(violation_type_str)
                        except ValueError:
                            continue
                    
                    if violation_type:
                        violations.append(ChartViolation(
                            violation_type=violation_type,
                            timestamp_start=ModelArkClient.safe_parse_datetime(
                                v.get("timestamp_start")
                            ),
                            timestamp_end=ModelArkClient.safe_parse_datetime(
                                v.get("timestamp_end")
                            ),
                            description=str(v.get("description", "")),
                            confidence=float(v.get("confidence", 0.5)),
                            extracted_value=v.get("extracted_value")
                        ))
                except (ValueError, TypeError, KeyError):
                    continue
        
        time_range = parsed.get("time_range", {}) or {}
        temp_range = parsed.get("temperature_range", {}) or {}
        
        data_points = self._extract_data_points(parsed)
        
        if not data_points:
            logger.info("No data points extracted, trying fallback generation from time_range")
            data_points = self._generate_fallback_points(parsed)
        
        return ChartAnalysisResult(
            model_used=settings.model_chart_analysis,
            analyzed_at=datetime.now(),
            duration_seconds=duration,
            chart_type=parsed.get("chart_type"),
            time_range_start=ModelArkClient.safe_parse_datetime(
                time_range.get("start") if isinstance(time_range, dict) else None
            ),
            time_range_end=ModelArkClient.safe_parse_datetime(
                time_range.get("end") if isinstance(time_range, dict) else None
            ),
            temp_range_min=float(temp_range.get("min")) if (
                isinstance(temp_range, dict) and temp_range.get("min") is not None
            ) else None,
            temp_range_max=float(temp_range.get("max")) if (
                isinstance(temp_range, dict) and temp_range.get("max") is not None
            ) else None,
            violations=violations,
            data_points=data_points,
            summary=str(parsed.get("summary", "")),
            raw_response=raw_response,
            confidence=float(parsed.get("confidence_score", 0.5))
        )
