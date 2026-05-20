from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict
import base64
import logging
import re

from app.ai.client import ModelArkClient, ImageFormat, AIValidationError
from app.ai.image.models import ChartAnalysisResult, TemperatureReading
from app.ai.image.analyzer import ChartAnalyzer
from app.models.logs import LogEntry, LogType
from app.models.multimodal import (
    ChartAlignment as ChartAlignmentModel,
    AlignmentMethod,
    ConfidenceLevel,
)
from app.multimodal.prompts import (
    SYSTEM_PROMPT_CHART_TIME_RANGE,
    USER_PROMPT_CHART_TIME_RANGE,
    SYSTEM_PROMPT_CHART_ALIGNMENT_VALIDATION,
    build_pattern_comparison_prompt,
    extract_log_patterns,
)
from app.config import settings

logger = logging.getLogger(__name__)


class AlignmentResult:
    def __init__(
        self,
        alignment: ChartAlignmentModel,
        aligned_data_points: List[TemperatureReading],
        pattern_matches: List[Dict[str, Any]],
        warnings: List[str],
    ):
        self.alignment = alignment
        self.aligned_data_points = aligned_data_points
        self.pattern_matches = pattern_matches
        self.warnings = warnings


class ChartAlignmentService:
    def __init__(self, client: Optional[ModelArkClient] = None):
        self.client = client or ModelArkClient()
        self.chart_analyzer = ChartAnalyzer(client=self.client)
        self.warnings: List[str] = []

    async def extract_time_range_from_chart(
        self,
        image_bytes: bytes,
        image_format: ImageFormat = ImageFormat.PNG,
    ) -> Tuple[Optional[datetime], Optional[datetime], float, Dict[str, Any]]:
        """
        Extract time range from a chart image using VLLM.
        
        Args:
            image_bytes: Chart image bytes
            image_format: PNG/JPG
        
        Returns:
            Tuple of (start_time, end_time, confidence, extra_info)
        """
        if not settings.ai_enabled:
            self.warnings.append("AI not enabled, cannot extract time range from chart")
            return None, None, 0.0, {"uncertain": True}

        if not self.client.validate_image_size(image_bytes):
            self.warnings.append("Image exceeds size limit")
            return None, None, 0.0, {"uncertain": True}

        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        format_str = "jpg" if image_format == ImageFormat.JPEG else image_format.value

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{SYSTEM_PROMPT_CHART_TIME_RANGE}\n\n{USER_PROMPT_CHART_TIME_RANGE}"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{format_str};base64,{image_base64}"
                        }
                    }
                ]
            }
        ]

        try:
            response = await self.client.chat_completion(
                messages=messages,
                model=settings.model_chart_analysis,
                response_format={"type": "json_object"}
            )

            content = self._extract_response_content(response)
            parsed = ModelArkClient.parse_json_response(content)

            time_range = parsed.get("time_range", {}) or {}
            confidence = float(parsed.get("confidence", 0.5))
            uncertain = parsed.get("uncertain", confidence < 0.7)

            start_time = ModelArkClient.safe_parse_datetime(
                time_range.get("start_time") if isinstance(time_range, dict) else None
            )
            end_time = ModelArkClient.safe_parse_datetime(
                time_range.get("end_time") if isinstance(time_range, dict) else None
            )

            extra_info = {
                "uncertain": uncertain,
                "reasoning": parsed.get("reasoning", ""),
                "time_format_notes": parsed.get("time_format_notes", {}),
            }

            if uncertain:
                self.warnings.append(
                    f"Chart time range extraction uncertain (confidence: {confidence:.2f})"
                )

            logger.info(
                f"Extracted time range from chart: {start_time} to {end_time}, confidence: {confidence}"
            )

            return start_time, end_time, confidence, extra_info

        except Exception as e:
            self.warnings.append(f"Failed to extract time range: {str(e)}")
            logger.error(f"Time range extraction failed: {e}")
            return None, None, 0.0, {"uncertain": True, "error": str(e)}

    def pattern_match_alignment(
        self,
        log_entries: List[LogEntry],
        chart_data_points: List[TemperatureReading],
        log_time_range: Tuple[Optional[datetime], Optional[datetime]],
        chart_llm_time_range: Tuple[Optional[datetime], Optional[datetime]],
    ) -> Tuple[float, timedelta, List[Dict[str, Any]]]:
        """
        Pattern-based alignment between log temperature curves and chart data.
        
        Args:
            log_entries: System log entries with timestamps
            chart_data_points: Chart-extracted data points (relative times)
            log_time_range: (min_time, max_time) from logs
            chart_llm_time_range: (start, end) from LLM chart analysis
        
        Returns:
            Tuple of (confidence, offset_seconds, pattern_matches)
        """
        log_temp_readings = self._extract_log_temperatures(log_entries)
        log_start, log_end = log_time_range
        chart_llm_start, chart_llm_end = chart_llm_time_range

        if not log_temp_readings or not chart_data_points:
            self.warnings.append("Not enough data for pattern matching")
            return 0.0, timedelta(seconds=0), []

        patterns = []

        door_spikes_log = self._find_door_spikes(log_temp_readings)
        door_spikes_chart = self._find_chart_temp_spikes(chart_data_points)

        excursions_log = self._find_temperature_excursions(log_temp_readings)
        excursions_chart = self._find_chart_excursions(chart_data_points)

        total_patterns = max(len(door_spikes_log) + len(excursions_log), 1)
        matches = []

        for chart_spike in door_spikes_chart:
            for log_spike in door_spikes_log:
                similarity = self._compare_pattern_shapes(
                    chart_spike.get("points", []),
                    log_spike.get("points", [])
                )
                if similarity > 0.7:
                    matches.append({
                        "pattern_type": "door_open_spike",
                        "chart_relative_index": chart_spike.get("index"),
                        "chart_relative_time": chart_spike.get("time"),
                        "log_time": log_spike.get("timestamp"),
                        "similarity": similarity,
                    })
                    break

        for chart_exc in excursions_chart:
            for log_exc in excursions_log:
                similarity = self._compare_pattern_shapes(
                    chart_exc.get("points", []),
                    log_exc.get("points", [])
                )
                if similarity > 0.7:
                    matches.append({
                        "pattern_type": "temperature_excursion",
                        "chart_relative_index": chart_exc.get("index"),
                        "chart_relative_time": chart_exc.get("time"),
                        "log_time": log_exc.get("timestamp"),
                        "similarity": similarity,
                    })
                    break

        if matches:
            confidence = self.calculate_pattern_confidence(
                len(matches),
                total_patterns,
                [m.get("similarity", 0.5) for m in matches]
            )

            avg_similarity = sum(m.get("similarity", 0.5) for m in matches) / len(matches)
            confidence = min(confidence * avg_similarity, 1.0)

            best_match = max(matches, key=lambda x: x.get("similarity", 0))
            offset = self._calculate_offset(best_match, log_start)

            return confidence, offset, matches

        if chart_llm_start and chart_llm_end and log_start and log_end:
            chart_duration = (chart_llm_end - chart_llm_start).total_seconds()
            log_duration = (log_end - log_start).total_seconds()
            
            duration_similarity = 1.0 - abs(chart_duration - log_duration) / max(chart_duration, log_duration, 1)
            
            if duration_similarity > 0.8:
                return 0.6 * duration_similarity, timedelta(seconds=0), []

        return 0.0, timedelta(seconds=0), []

    def calculate_pattern_confidence(
        self,
        match_count: int,
        total_patterns: int,
        similarities: List[float],
    ) -> float:
        """
        Calculate alignment confidence based on pattern matching.
        
        Thresholds:
        - ≥ 0.85 → HIGH confidence
        - 0.70-0.84 → MEDIUM confidence
        - < 0.70 → LOW/UNCERTAIN
        """
        if total_patterns == 0:
            return 0.0

        match_ratio = match_count / total_patterns
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.5

        base_confidence = (match_ratio * 0.6) + (avg_similarity * 0.4)

        if match_count >= 3:
            base_confidence = min(base_confidence * 1.15, 1.0)
        elif match_count >= 2:
            base_confidence = min(base_confidence * 1.05, 1.0)

        return round(base_confidence, 2)

    def align_chart_data_points(
        self,
        data_points: List[TemperatureReading],
        alignment_start: datetime,
        chart_duration_seconds: Optional[float] = None,
    ) -> List[TemperatureReading]:
        """
        Map chart data points from relative time to absolute timestamps.
        
        Args:
            data_points: Chart data points with relative "time" field (HH:MM format)
            alignment_start: The absolute start time for alignment
            chart_duration_seconds: Optional total duration for scaling
        
        Returns:
            Data points with absolute timestamps
        """
        if not data_points:
            return []

        sorted_points = sorted(data_points, key=lambda p: p.time)

        first_time = self._parse_hhmm(sorted_points[0].time)
        if first_time is None:
            first_seconds = 0
        else:
            first_hours, first_mins = first_time
            first_seconds = first_hours * 3600 + first_mins * 60

        aligned_points = []

        for point in sorted_points:
            parsed = self._parse_hhmm(point.time)
            
            if parsed is None:
                aligned_points.append(point)
                continue

            hours, mins = parsed
            point_seconds = hours * 3600 + mins * 60
            relative_seconds = point_seconds - first_seconds

            absolute_time = alignment_start + timedelta(seconds=relative_seconds)

            aligned_point = TemperatureReading(
                time=point.time,
                timestamp=absolute_time,
                sensor_a=point.sensor_a,
                sensor_b=point.sensor_b,
                source=point.source,
            )
            aligned_points.append(aligned_point)

        return aligned_points

    async def align_chart(
        self,
        log_entries: List[LogEntry],
        image_bytes: Optional[bytes] = None,
        image_format: ImageFormat = ImageFormat.PNG,
        chart_result: Optional[Any] = None,
    ) -> AlignmentResult:
        """
        Full chart alignment workflow:
        1. Analyze chart (or use pre-analyzed result) to get data points and time range
        2. Try pattern matching first (if logs available and confidence > 0.8)
        3. Fall back to LLM-extracted time range
        4. Mark uncertain if confidence < 0.7
        
        Args:
            log_entries: System log entries for pattern matching
            image_bytes: Chart image bytes (optional if chart_result provided)
            image_format: Image format
            chart_result: Pre-analyzed ChartAnalysisResult (to skip redundant VLLM call)
        
        Returns:
            AlignmentResult with alignment info and aligned data points
        """
        self.warnings = []

        if chart_result is None:
            if image_bytes is None:
                self.warnings.append("No chart data provided")
                return AlignmentResult(
                    alignment=ChartAlignmentModel(
                        method=AlignmentMethod.LLM_EXTRACTED,
                        confidence=0.0,
                        uncertain=True,
                    ),
                    aligned_data_points=[],
                    pattern_matches=[],
                    warnings=list(self.warnings),
                )
            try:
                chart_result = await self.chart_analyzer.analyze(image_bytes, image_format)
            except Exception as e:
                self.warnings.append(f"Chart analysis failed: {str(e)}")
                return AlignmentResult(
                    alignment=ChartAlignmentModel(
                        method=AlignmentMethod.LLM_EXTRACTED,
                        confidence=0.0,
                        uncertain=True,
                    ),
                    aligned_data_points=[],
                    pattern_matches=[],
                    warnings=list(self.warnings),
                )

        data_points = chart_result.data_points
        chart_llm_start = chart_result.time_range_start
        chart_llm_end = chart_result.time_range_end

        log_start, log_end = self._get_log_time_range(log_entries)

        use_alignment: Optional[datetime] = None
        alignment_method = AlignmentMethod.LLM_EXTRACTED
        final_confidence = 0.5
        pattern_matches: List[Dict[str, Any]] = []

        if log_entries and data_points and log_start:
            pattern_confidence, offset, matches = self.pattern_match_alignment(
                log_entries=log_entries,
                chart_data_points=data_points,
                log_time_range=(log_start, log_end),
                chart_llm_time_range=(chart_llm_start, chart_llm_end),
            )

            if pattern_confidence > 0.8:
                alignment_method = AlignmentMethod.PATTERN_MATCHED
                final_confidence = pattern_confidence
                pattern_matches = matches

                if chart_llm_start:
                    use_alignment = chart_llm_start + offset
                elif log_start:
                    use_alignment = log_start + offset
                else:
                    use_alignment = chart_llm_start
            else:
                if pattern_confidence > 0:
                    self.warnings.append(
                        f"Pattern matching confidence {pattern_confidence:.2f} too low, using LLM extraction"
                    )

        if use_alignment is None and chart_llm_start:
            use_alignment = chart_llm_start
            final_confidence = chart_result.confidence
            alignment_method = AlignmentMethod.LLM_EXTRACTED
        elif use_alignment is None and log_start:
            use_alignment = log_start
            final_confidence = 0.3
            alignment_method = AlignmentMethod.LLM_EXTRACTED
            self.warnings.append("No chart time range available, using log start time as fallback")

        aligned_points = []
        if use_alignment:
            chart_duration = None
            if chart_llm_start and chart_llm_end:
                chart_duration = (chart_llm_end - chart_llm_start).total_seconds()
            
            aligned_points = self.align_chart_data_points(
                data_points=data_points,
                alignment_start=use_alignment,
                chart_duration_seconds=chart_duration,
            )

        uncertain = final_confidence < 0.7

        if uncertain:
            self.warnings.append(
                f"Alignment uncertain (confidence: {final_confidence:.2f} < 0.7 threshold)"
            )

        alignment_end = None
        if aligned_points:
            timestamps = [p.timestamp for p in aligned_points if p.timestamp]
            if timestamps:
                alignment_end = max(timestamps)

        alignment = ChartAlignmentModel(
            method=alignment_method,
            confidence=final_confidence,
            start_time=use_alignment,
            end_time=alignment_end,
            uncertain=uncertain,
        )

        logger.info(
            f"Chart alignment complete: method={alignment_method.value}, "
            f"confidence={final_confidence:.2f}, uncertain={uncertain}"
        )

        return AlignmentResult(
            alignment=alignment,
            aligned_data_points=aligned_points,
            pattern_matches=pattern_matches,
            warnings=list(self.warnings),
        )

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

    def _extract_log_temperatures(
        self, entries: List[LogEntry]
    ) -> List[Dict[str, Any]]:
        """Extract temperature readings from log entries."""
        temps = []
        for entry in entries:
            if entry.log_type == LogType.TEMP_READING and entry.parsed_value is not None:
                temps.append({
                    "timestamp": entry.timestamp,
                    "temperature": float(entry.parsed_value),
                    "raw_value": entry.raw_value,
                })
        return sorted(temps, key=lambda x: x["timestamp"])

    def _get_log_time_range(
        self, entries: List[LogEntry]
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        if not entries:
            return None, None
        timestamps = [e.timestamp for e in entries]
        return min(timestamps), max(timestamps)

    def _find_door_spikes(
        self, temp_readings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find door open patterns (sudden temperature rise followed by recovery)."""
        spikes = []
        
        for i in range(2, len(temp_readings)):
            prev = temp_readings[i-2]
            curr = temp_readings[i-1]
            next_read = temp_readings[i]
            
            rise = curr["temperature"] - prev["temperature"]
            
            if rise > 1.0 and 2.0 <= prev["temperature"] <= 8.0:
                spikes.append({
                    "index": i-1,
                    "timestamp": curr["timestamp"],
                    "temperature": curr["temperature"],
                    "rise_amount": rise,
                    "points": [prev, curr, next_read] if i < len(temp_readings) else [prev, curr],
                })
        
        return spikes

    def _find_chart_temp_spikes(
        self, data_points: List[TemperatureReading]
    ) -> List[Dict[str, Any]]:
        """Find temperature spikes in chart data."""
        spikes = []
        
        for i in range(2, len(data_points)):
            prev = data_points[i-2]
            curr = data_points[i-1]
            next_read = data_points[i]
            
            rise = curr.sensor_a - prev.sensor_a
            
            if rise > 1.0 and 2.0 <= prev.sensor_a <= 8.0:
                spikes.append({
                    "index": i-1,
                    "time": curr.time,
                    "temperature": curr.sensor_a,
                    "rise_amount": rise,
                    "points": [
                        {"temp": prev.sensor_a, "time": prev.time},
                        {"temp": curr.sensor_a, "time": curr.time},
                        {"temp": next_read.sensor_a, "time": next_read.time},
                    ],
                })
        
        return spikes

    def _find_temperature_excursions(
        self, temp_readings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find temperatures outside 2-8°C range."""
        excursions = []
        
        for i, reading in enumerate(temp_readings):
            temp = reading["temperature"]
            if temp < 2.0 or temp > 8.0:
                excursions.append({
                    "index": i,
                    "timestamp": reading["timestamp"],
                    "temperature": temp,
                    "points": [reading],
                })
        
        return excursions

    def _find_chart_excursions(
        self, data_points: List[TemperatureReading]
    ) -> List[Dict[str, Any]]:
        """Find chart temperatures outside 2-8°C range."""
        excursions = []
        
        for i, point in enumerate(data_points):
            temp = point.sensor_a
            if temp < 2.0 or temp > 8.0:
                excursions.append({
                    "index": i,
                    "time": point.time,
                    "temperature": temp,
                    "points": [{"temp": temp, "time": point.time}],
                })
        
        return excursions

    def _compare_pattern_shapes(
        self, pattern1: List[Dict[str, Any]], pattern2: List[Dict[str, Any]]
    ) -> float:
        """Compare two patterns for shape similarity (0.0 to 1.0)."""
        if not pattern1 or not pattern2:
            return 0.0

        temps1 = [p.get("temperature", p.get("temp", 0.0)) for p in pattern1]
        temps2 = [p.get("temperature", p.get("temp", 0.0)) for p in pattern2]

        if len(temps1) < 2 or len(temps2) < 2:
            return 0.5

        delta1 = [temps1[i] - temps1[i-1] for i in range(1, len(temps1))]
        delta2 = [temps2[i] - temps2[i-1] for i in range(1, len(temps2))]

        min_len = min(len(delta1), len(delta2))
        if min_len == 0:
            return 0.0

        similarity = 0.0
        for i in range(min_len):
            d1, d2 = delta1[i], delta2[i]
            if abs(d1) < 0.1 and abs(d2) < 0.1:
                similarity += 1.0
            elif (d1 > 0 and d2 > 0) or (d1 < 0 and d2 < 0):
                ratio = min(abs(d1), abs(d2)) / max(abs(d1), abs(d2), 0.1)
                similarity += 0.5 + (ratio * 0.5)
            else:
                similarity += 0.0

        return similarity / min_len

    def _calculate_offset(
        self, match: Dict[str, Any], log_start: Optional[datetime]
    ) -> timedelta:
        """Calculate time offset between chart relative time and log absolute time."""
        chart_time_str = match.get("chart_relative_time", "00:00")
        log_time = match.get("log_time")

        if log_time and log_start:
            chart_parsed = self._parse_hhmm(chart_time_str)
            if chart_parsed:
                chart_seconds = chart_parsed[0] * 3600 + chart_parsed[1] * 60
                log_seconds = (log_time - log_start).total_seconds()
                return timedelta(seconds=log_seconds - chart_seconds)

        return timedelta(seconds=0)

    def _parse_hhmm(self, time_str: str) -> Optional[Tuple[int, int]]:
        """Parse HH:MM format time string."""
        if not time_str:
            return None

        match = re.match(r'(\d{1,2}):(\d{2})', time_str.strip())
        if match:
            return int(match.group(1)), int(match.group(2))

        return None
