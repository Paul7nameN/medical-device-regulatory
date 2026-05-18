import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

from app.ai.client import (
    AIError,
    AIValidationError,
    ModelArkClient,
    ImageFormat,
)


class TestAIEndpoints:
    @pytest.fixture
    def test_client(self):
        from app.main import app
        return TestClient(app)
    
    def test_get_ai_models_disabled(self, test_client):
        with patch('app.config.settings.ai_enabled', False):
            with patch('app.config.settings.modelark_api_key', None):
                response = test_client.get("/api/ai/models")
                
                assert response.status_code == 200
                data = response.json()
                
                assert "models" in data
                assert data["api_status"] == "not_configured"
    
    def test_get_ai_models_enabled(self, test_client):
        with patch('app.config.settings.ai_enabled', True):
            with patch('app.config.settings.modelark_api_key', "test-key"):
                with patch('app.config.settings.modelark_base_url', "https://test.api"):
                    response = test_client.get("/api/ai/models")
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert "models" in data
                    assert len(data["models"]) == 2
                    assert "api_status" in data
                    assert "config" in data
    
    def test_get_ai_models_config(self, test_client):
        with patch('app.config.settings.ai_enabled', True):
            with patch('app.config.settings.modelark_api_key', "test-key"):
                with patch('app.config.settings.modelark_timeout', 60):
                    with patch('app.config.settings.modelark_max_retries', 3):
                        response = test_client.get("/api/ai/models")
                        
                        assert response.status_code == 200
                        data = response.json()
                        
                        assert data["config"]["timeout"] == 60
                        assert data["config"]["max_retries"] == 3


class TestFormatErrorResponse:
    def test_format_error_response_validation(self):
        from app.api.ai import _format_error_response
        from app.ai.client import AIValidationError
        
        error = AIValidationError("Invalid input")
        response = _format_error_response(error)
        
        assert response.error_type == "validation_error"
        assert response.message == "Invalid input"
        assert response.retry_available == False
    
    def test_format_error_response_rate_limit(self):
        from app.api.ai import _format_error_response
        from app.ai.client import AIRateLimitError
        
        error = AIRateLimitError("Rate limit exceeded", retry_after=60)
        response = _format_error_response(error)
        
        assert response.error_type == "rate_limit"
        assert response.retry_available == True
        assert response.retry_after_seconds == 60
    
    def test_format_error_response_timeout(self):
        from app.api.ai import _format_error_response
        from app.ai.client import AITimeoutError
        
        error = AITimeoutError("Request timed out")
        response = _format_error_response(error)
        
        assert response.error_type == "timeout"
        assert response.retry_available == True


class TestAIEndpointErrorHandling:
    def test_ai_analysis_not_enabled(self):
        from app.api.ai import _format_error_response
        from app.ai.client import AIValidationError
        
        error = AIValidationError("AI analysis not enabled")
        response = _format_error_response(error)
        
        assert response.error_type == "validation_error"
        assert "not enabled" in response.message.lower()


class TestAIEndpointModels:
    def test_log_entry_input_model(self):
        from app.api.ai import LogEntryInput
        
        entry = LogEntryInput(
            timestamp="2026-05-14T14:00:00",
            log_type="TEMP_READING",
            raw_value="4.3C",
            parsed_value=4.3
        )
        
        assert entry.timestamp == "2026-05-14T14:00:00"
        assert entry.log_type == "TEMP_READING"
        assert entry.raw_value == "4.3C"
        assert entry.parsed_value == 4.3
    
    def test_finding_input_model(self):
        from app.api.ai import FindingInput
        
        finding = FindingInput(
            rule_id="REG-TEMP-1",
            rule_description="Temperature range",
            category="thermal",
            severity="high",
            passed=False,
            message="Temperature out of range"
        )
        
        assert finding.rule_id == "REG-TEMP-1"
        assert finding.severity == "high"
        assert finding.passed == False
    
    def test_log_analysis_request_model(self):
        from app.api.ai import LogAnalysisRequest
        
        request = LogAnalysisRequest(
            logs=[],
            findings=[],
            raw_logs=["2026-05-14 14:00:10 TEMP_READING 4.3C"],
            device_id="test"
        )
        
        assert request.raw_logs is not None
        assert request.device_id == "test"
    
    def test_report_generation_request_model(self):
        from app.api.ai import ReportGenerationRequest
        
        request = ReportGenerationRequest(
            device_id="test-device",
            total_entries=100,
            passed_count=8,
            failed_count=2,
            critical_count=1,
            report_type="compliance_summary"
        )
        
        assert request.device_id == "test-device"
        assert request.total_entries == 100
        assert request.report_type == "compliance_summary"
