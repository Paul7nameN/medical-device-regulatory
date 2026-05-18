import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from collections import defaultdict

from app.ai.text.models import (
    LogAnalysisResult,
    ComplianceReportSection,
    GeneratedReport,
    AIErrorResponse,
)
from app.ai.text.analyzer import TextAnalyzer
from app.ai.text.prompts import (
    SYSTEM_PROMPT_LOG_ANALYSIS,
    SYSTEM_PROMPT_REPORT_GENERATION,
    LOG_ANALYSIS_USER_PROMPT_TEMPLATE,
    REPORT_GENERATION_USER_PROMPT_TEMPLATE,
)
from app.ai.client import ModelArkClient


class TestTextAnalysisModels:
    def test_log_analysis_result_creation(self):
        result = LogAnalysisResult(
            model_used="test-model",
            analyzed_at=datetime(2026, 5, 14, 14, 30, 0),
            duration_seconds=3.5,
            summary="Device operating normally",
            key_findings=["Temperature stable", "No sensor issues"],
            recommendations=["Continue monitoring"],
            risk_assessment="low"
        )
        
        assert result.model_used == "test-model"
        assert result.summary == "Device operating normally"
        assert len(result.key_findings) == 2
        assert len(result.recommendations) == 1
        assert result.risk_assessment == "low"
    
    def test_compliance_report_section_creation(self):
        section = ComplianceReportSection(
            title="Executive Summary",
            content="Device passed all critical tests",
            bullet_points=["No temperature excursions", "Sensors operational"]
        )
        
        assert section.title == "Executive Summary"
        assert section.content == "Device passed all critical tests"
        assert len(section.bullet_points) == 2
    
    def test_compliance_report_section_no_bullets(self):
        section = ComplianceReportSection(
            title="Summary",
            content="No bullet points needed"
        )
        
        assert section.bullet_points is None
    
    def test_generated_report_creation(self):
        report = GeneratedReport(
            model_used="test-model",
            generated_at=datetime(2026, 5, 14, 14, 30, 0),
            duration_seconds=10.5,
            report_type="compliance_summary",
            device_id="CRYOSAFE-001",
            title="MED-THERM Compliance Report",
            sections=[
                ComplianceReportSection(
                    title="Section 1",
                    content="Content"
                )
            ],
            executive_summary="Executive summary content",
            recommendations="Recommendations content",
            conclusion="Conclusion content"
        )
        
        assert report.device_id == "CRYOSAFE-001"
        assert report.report_type == "compliance_summary"
        assert len(report.sections) == 1
        assert report.executive_summary == "Executive summary content"
    
    def test_ai_error_response_creation(self):
        error = AIErrorResponse(
            error_type="validation_error",
            message="Invalid input provided",
            retry_available=False,
            retry_after_seconds=None
        )
        
        assert error.error_type == "validation_error"
        assert error.message == "Invalid input provided"
        assert error.retry_available == False
    
    def test_ai_error_response_with_retry(self):
        error = AIErrorResponse(
            error_type="rate_limit",
            message="Rate limit exceeded",
            retry_available=True,
            retry_after_seconds=60
        )
        
        assert error.retry_available == True
        assert error.retry_after_seconds == 60


class TestTextPrompts:
    def test_log_analysis_prompt_contains_types(self):
        assert "TEMP_READING" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "SENSOR_TIMEOUT" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "ALARM_TRIGGERED" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "DOOR_OPEN" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "DOOR_CLOSE" in SYSTEM_PROMPT_LOG_ANALYSIS
    
    def test_log_analysis_prompt_contains_regulations(self):
        assert "REG-TEMP-1" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "REG-TEMP-2" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "REG-TEMP-3" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "REG-TEMP-4" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "REG-SENS-1" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "REG-ALARM-1" in SYSTEM_PROMPT_LOG_ANALYSIS
        assert "REG-DATA-2" in SYSTEM_PROMPT_LOG_ANALYSIS
    
    def test_report_generation_prompt_exists(self):
        assert SYSTEM_PROMPT_REPORT_GENERATION is not None
        assert "EXECUTIVE SUMMARY" in SYSTEM_PROMPT_REPORT_GENERATION.upper()
        assert "RECOMMENDATIONS" in SYSTEM_PROMPT_REPORT_GENERATION.upper()
        assert "CONCLUSION" in SYSTEM_PROMPT_REPORT_GENERATION.upper()
    
    def test_user_prompt_templates_exist(self):
        assert LOG_ANALYSIS_USER_PROMPT_TEMPLATE is not None
        assert REPORT_GENERATION_USER_PROMPT_TEMPLATE is not None


class TestTextAnalyzer:
    def test_analyzer_init(self):
        mock_client = MagicMock(spec=ModelArkClient)
        analyzer = TextAnalyzer(mock_client)
        assert analyzer.client == mock_client
    
    def test_analyzer_init_default_client(self):
        with patch('app.config.settings', new=MagicMock()):
            with patch('app.ai.text.analyzer.ModelArkClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                analyzer = TextAnalyzer()
                
                mock_client_class.assert_called_once()
                assert analyzer.client == mock_client


class TestTextAnalyzerLogSummarization:
    def test_summarize_logs_empty(self):
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(TextAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            result = analyzer._summarize_logs([])
            
            assert "No log entries" in result
    
    def test_summarize_logs_with_entries(self):
        class MockLogEntry:
            def __init__(self, log_type_val):
                self.log_type = log_type_val
        
        from app.ai.text.analyzer import TextAnalyzer
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(TextAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            logs = [
                MockLogEntry("TEMP_READING"),
                MockLogEntry("TEMP_READING"),
                MockLogEntry("FAN_SPEED"),
                MockLogEntry("ALARM_TRIGGERED"),
            ]
            
            result = analyzer._summarize_logs(logs)
            
            assert "Total log entries: 4" in result
            assert "TEMP_READING" in result
            assert "FAN_SPEED" in result
            assert "ALARM_TRIGGERED" in result


class TestTextAnalyzerExtractMethods:
    def test_extract_response_content(self):
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"summary": "Test summary"}'
                    }
                }
            ]
        }
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(TextAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            content = analyzer._extract_response_content(mock_response)
            assert content == '{"summary": "Test summary"}'
    
    def test_extract_response_content_empty(self):
        mock_response = {"choices": []}
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(TextAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            content = analyzer._extract_response_content(mock_response)
            assert content == '{}'


class TestTextAnalyzerFormatting:
    def test_format_category_breakdown(self):
        summary_dict = {
            "thermal": {"passed": 2, "failed": 1, "total": 3},
            "sensor": {"passed": 1, "failed": 1, "total": 2}
        }
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(TextAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            result = analyzer._format_category_breakdown(summary_dict)
            
            assert "thermal" in result
            assert "2 passed" in result
            assert "1 failed" in result
            assert "sensor" in result
    
    def test_format_category_breakdown_empty(self):
        with patch.object(ModelArkClient, '__init__', return_value=None):
            analyzer = object.__new__(TextAnalyzer)
            analyzer.client = object.__new__(ModelArkClient)
            
            result = analyzer._format_category_breakdown({})
            
            assert "No category breakdown" in result or result == "No category breakdown available."


class TestTextAnalyzerAsyncBehavior:
    @pytest.mark.asyncio
    async def test_analyze_logs_calls_client(self):
        mock_client = MagicMock(spec=ModelArkClient)
        mock_client.analyze_text = AsyncMock(return_value={
            "choices": [
                {"message": {"content": '{"summary": "Test", "key_findings": [], "recommendations": [], "risk_assessment": "low"}'}}
            ]
        })
        
        with patch('app.config.settings', new=MagicMock()):
            with patch('app.config.settings.ai_enabled', True):
                analyzer = TextAnalyzer(mock_client)
                
                result = await analyzer.analyze_logs([], [])
                
                mock_client.analyze_text.assert_called_once()
