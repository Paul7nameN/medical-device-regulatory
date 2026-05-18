import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.ai.integration.engine import (
    AIAugmentedRegulatoryEngine,
    validate_with_ai,
)
from app.ai.client import (
    ModelArkClient,
    AIValidationError,
)
from app.ai.image.models import (
    ChartViolation,
    ChartViolationType,
)
from app.config import settings


class TestAIAugmentedRegulatoryEngine:
    def test_init(self):
        mock_engine = MagicMock()
        mock_client = MagicMock(spec=ModelArkClient)
        
        engine = AIAugmentedRegulatoryEngine(
            base_engine=mock_engine,
            client=mock_client
        )
        
        assert engine.base_engine == mock_engine
        assert engine.client == mock_client
    
    def test_init_defaults(self):
        with patch('app.ai.integration.engine.RegulatoryEngine') as mock_engine_class:
            with patch('app.ai.integration.engine.ModelArkClient') as mock_client_class:
                mock_engine = MagicMock()
                mock_client = MagicMock()
                mock_engine_class.return_value = mock_engine
                mock_client_class.return_value = mock_client
                
                engine = AIAugmentedRegulatoryEngine()
                
                mock_engine_class.assert_called_once()
                mock_client_class.assert_called_once()


class TestCrossValidation:
    def test_cross_validate_no_violations(self):
        class MockFinding:
            def __init__(self, passed, severity_val, rule_id_val):
                self.passed = passed
                self.severity = severity_val
                self.rule_id = rule_id_val
        
        class MockChartResult:
            def __init__(self, violations_list):
                self.violations = violations_list
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            engine = object.__new__(AIAugmentedRegulatoryEngine)
            engine.base_engine = object.__new__(object)
            engine.client = object.__new__(ModelArkClient)
            
            result = engine._cross_validate(
                log_findings=[],
                chart_result=MockChartResult([])
            )
            
            assert result.log_findings_count == 0
            assert result.chart_findings_count == 0
            assert result.matching_violations == 0
            assert result.confidence_score == 1.0
    
    def test_cross_validate_with_temp_violations(self):
        from app.ai.integration.engine import AIAugmentedRegulatoryEngine
        
        class MockFinding:
            def __init__(self, passed, severity_val, rule_id_val):
                self.passed = passed
                self.severity = severity_val
                self.rule_id = rule_id_val
        
        class MockChartResult:
            def __init__(self, violations_list):
                self.violations = violations_list
        
        from app.models.findings import Severity
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            engine = object.__new__(AIAugmentedRegulatoryEngine)
            engine.base_engine = object.__new__(object)
            engine.client = object.__new__(ModelArkClient)
            
            log_findings = [
                MockFinding(passed=False, severity_val=Severity.HIGH, rule_id_val="REG-TEMP-1")
            ]
            
            chart_violations = [
                ChartViolation(
                    violation_type=ChartViolationType.EXCURSION,
                    description="Test",
                    confidence=0.9
                )
            ]
            
            result = engine._cross_validate(
                log_findings=log_findings,
                chart_result=MockChartResult(chart_violations)
            )
            
            assert result.log_findings_count == 1
            assert result.chart_findings_count == 1
            assert result.matching_violations == 1
            assert "matching" in result.summary.lower()


class TestValidateWithAI:
    @pytest.mark.asyncio
    async def test_validate_with_ai_empty_logs(self):
        with patch('app.ai.integration.engine.RegulatoryEngine') as mock_engine_class:
            with patch('app.config.settings', new=MagicMock()):
                mock_engine = MagicMock()
                mock_engine.validate.return_value = MagicMock()
                mock_engine_class.return_value = mock_engine
                
                result = await validate_with_ai(
                    logs=[],
                    device_id="test"
                )
                
                assert result["report"] is not None
                assert result["ai_enabled"] is not None
    
    @pytest.mark.asyncio
    async def test_validate_with_ai_without_ai_enabled(self):
        from app.config import Settings
        from app.ai.integration.engine import validate_with_ai
        
        with patch('app.ai.integration.engine.RegulatoryEngine') as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.validate.return_value = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            with patch('app.config.settings.ai_enabled', False):
                with patch('app.config.settings.modelark_api_key', None):
                    result = await validate_with_ai(
                        logs=[],
                        device_id="test"
                    )
                    
                    assert "warnings" in result
                    assert result["ai_enabled"] == False
    
    @pytest.mark.asyncio
    async def test_validate_with_ai_ai_required_raises(self):
        from app.ai.integration.engine import validate_with_ai, AIValidationError
        
        with patch('app.ai.integration.engine.RegulatoryEngine') as mock_engine_class:
            with patch('app.config.settings', new=MagicMock()):
                mock_engine = MagicMock()
                mock_engine_class.return_value = mock_engine
                
                with patch('app.config.settings.ai_enabled', False):
                    with patch('app.config.settings.modelark_api_key', None):
                        with pytest.raises(AIValidationError):
                            await validate_with_ai(
                                logs=[],
                                device_id="test",
                                ai_required=True
                            )


class TestCreateEmptyResult:
    def test_create_empty_result(self):
        from app.ai.integration.engine import AIAugmentedRegulatoryEngine
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            engine = object.__new__(AIAugmentedRegulatoryEngine)
            
            result = engine._create_empty_result("test-device")
            
            assert result["device_id"] == "test-device"
            assert result["total_entries"] == 0
            assert result["passed_count"] == 0
            assert result["failed_count"] == 0
