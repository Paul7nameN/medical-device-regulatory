import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.ai.image.models import (
    ChartAnalysisResult,
    ChartViolation,
    CrossValidationResult,
    ChartViolationType,
)
from app.ai.image.analyzer import ChartAnalyzer
from app.ai.image.prompts import (
    SYSTEM_PROMPT_CHART_ANALYSIS,
    IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE,
)
from app.ai.client import ModelArkClient, ImageFormat


class TestChartAnalysisModels:
    def test_chart_violation_creation(self):
        violation = ChartViolation(
            violation_type=ChartViolationType.EXCURSION,
            timestamp_start=datetime(2026, 5, 14, 14, 0, 0),
            timestamp_end=datetime(2026, 5, 14, 14, 15, 0),
            description="Temperature exceeded 8°C",
            confidence=0.95,
            extracted_value=9.5
        )
        
        assert violation.violation_type == ChartViolationType.EXCURSION
        assert violation.description == "Temperature exceeded 8°C"
        assert violation.confidence == 0.95
        assert violation.extracted_value == 9.5
    
    def test_chart_analysis_result_creation(self):
        result = ChartAnalysisResult(
            model_used="test-model",
            analyzed_at=datetime(2026, 5, 14, 14, 30, 0),
            duration_seconds=5.2,
            chart_type="temperature_profile",
            time_range_start=datetime(2026, 5, 14, 14, 0, 0),
            time_range_end=datetime(2026, 5, 14, 18, 0, 0),
            temp_range_min=0.0,
            temp_range_max=12.0,
            violations=[],
            summary="Chart analysis complete",
            confidence=0.9
        )
        
        assert result.model_used == "test-model"
        assert result.duration_seconds == 5.2
        assert result.chart_type == "temperature_profile"
        assert len(result.violations) == 0
        assert result.confidence == 0.9
    
    def test_cross_validation_result_creation(self):
        result = CrossValidationResult(
            log_findings_count=5,
            chart_findings_count=4,
            matching_violations=3,
            conflicting_findings=1,
            confidence_score=0.75,
            summary="3 matching violations found"
        )
        
        assert result.log_findings_count == 5
        assert result.chart_findings_count == 4
        assert result.matching_violations == 3
        assert result.conflicting_findings == 1
        assert result.confidence_score == 0.75


class TestImagePrompts:
    def test_system_prompt_contains_requirements(self):
        assert "MED-THERM-2026" in SYSTEM_PROMPT_CHART_ANALYSIS
        assert "REG-TEMP-1" in SYSTEM_PROMPT_CHART_ANALYSIS
        assert "REG-TEMP-2" in SYSTEM_PROMPT_CHART_ANALYSIS
        assert "REG-TEMP-3" in SYSTEM_PROMPT_CHART_ANALYSIS
        assert "REG-TEMP-4" in SYSTEM_PROMPT_CHART_ANALYSIS
        assert "REG-OPS-1" in SYSTEM_PROMPT_CHART_ANALYSIS
    
    def test_system_prompt_contains_violation_types(self):
        assert "excursion" in SYSTEM_PROMPT_CHART_ANALYSIS.lower()
        assert "gap" in SYSTEM_PROMPT_CHART_ANALYSIS.lower()
        assert "recovery" in SYSTEM_PROMPT_CHART_ANALYSIS.lower()
    
    def test_user_prompt_template_exists(self):
        assert IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE is not None
        assert len(IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE) > 0


class TestChartAnalyzer:
    def test_analyzer_init(self):
        mock_client = MagicMock(spec=ModelArkClient)
        analyzer = ChartAnalyzer(mock_client)
        assert analyzer.client == mock_client
    
    def test_analyzer_init_default_client(self):
        with patch('app.config.settings', new=MagicMock()):
            with patch('app.ai.image.analyzer.ModelArkClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                analyzer = ChartAnalyzer()
                
                mock_client_class.assert_called_once()
                assert analyzer.client == mock_client
    
    def test_extract_response_content(self):
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"chart_type": "temperature_profile"}'
                    }
                }
            ]
        }
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(ChartAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            content = analyzer._extract_response_content(mock_response)
            assert content == '{"chart_type": "temperature_profile"}'
    
    def test_extract_response_content_empty(self):
        mock_response = {"choices": []}
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(ChartAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            content = analyzer._extract_response_content(mock_response)
            assert content == '{}'


class TestChartAnalyzerBuildResult:
    def test_build_result_with_valid_data(self):
        parsed_data = {
            "chart_type": "temperature_profile",
            "time_range": {
                "start": "2026-05-14T14:00:00",
                "end": "2026-05-14T18:00:00"
            },
            "temperature_range": {
                "min": 0.0,
                "max": 12.0
            },
            "violations": [
                {
                    "violation_type": "excursion",
                    "timestamp_start": "2026-05-14T14:30:00",
                    "timestamp_end": "2026-05-14T14:45:00",
                    "description": "Temperature exceeded 8°C",
                    "confidence": 0.95,
                    "extracted_value": 9.5
                }
            ],
            "summary": "One excursion detected",
            "confidence_score": 0.9
        }
        
        raw_response = {"choices": []}
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(ChartAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            result = analyzer._build_result(parsed_data, raw_response, 5.2)
            
            assert result.chart_type == "temperature_profile"
            assert len(result.violations) == 1
            assert result.violations[0].violation_type == ChartViolationType.EXCURSION
            assert result.violations[0].confidence == 0.95
            assert result.summary == "One excursion detected"
            assert result.confidence == 0.9
    
    def test_build_result_with_no_violations(self):
        parsed_data = {
            "chart_type": "temperature_profile",
            "time_range": {"start": None, "end": None},
            "temperature_range": {"min": None, "max": None},
            "violations": [],
            "summary": "No violations detected",
            "confidence_score": 1.0
        }
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(ChartAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            result = analyzer._build_result(parsed_data, {}, 1.0)
            
            assert len(result.violations) == 0
            assert result.summary == "No violations detected"
    
    def test_build_result_with_invalid_violation_type(self):
        parsed_data = {
            "chart_type": "temperature_profile",
            "time_range": {},
            "temperature_range": {},
            "violations": [
                {
                    "violation_type": "invalid_type",
                    "description": "Invalid"
                }
            ],
            "summary": "Test",
            "confidence_score": 0.5
        }
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(ChartAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            result = analyzer._build_result(parsed_data, {}, 1.0)
            
            assert len(result.violations) == 0
    
    def test_build_result_with_partial_timestamps(self):
        parsed_data = {
            "chart_type": "temperature_profile",
            "time_range": None,
            "temperature_range": None,
            "violations": [
                {
                    "violation_type": "gap",
                    "timestamp_start": None,
                    "timestamp_end": None,
                    "description": "Gap detected",
                    "confidence": 0.8
                }
            ],
            "summary": "Test",
            "confidence_score": 0.8
        }
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(ChartAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            result = analyzer._build_result(parsed_data, {}, 1.0)
            
            assert len(result.violations) == 1
            assert result.violations[0].violation_type == ChartViolationType.GAP
            assert result.violations[0].timestamp_start is None


class TestChartAnalyzerAsyncBehavior:
    @pytest.mark.asyncio
    async def test_analyze_calls_client(self):
        mock_client = MagicMock(spec=ModelArkClient)
        mock_client.analyze_image = AsyncMock(return_value={
            "choices": [
                {"message": {"content": '{"chart_type": "test"}'}}
            ]
        })
        
        with patch('app.config.settings', new=MagicMock()):
            with patch('app.config.settings.ai_enabled', True):
                analyzer = ChartAnalyzer(mock_client)
                
                test_image = b"test image bytes"
                
                result = await analyzer.analyze(
                    test_image,
                    ImageFormat.PNG
                )
                
                mock_client.analyze_image.assert_called_once()
                assert mock_client.analyze_image.call_args[1]["image_format"] == ImageFormat.PNG
