import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.ai.client import (
    ModelArkClient,
    AIError,
    AIAPIError,
    AITimeoutError,
    AIRateLimitError,
    AIValidationError,
    AIImageError,
    ImageFormat,
    ChartViolationType,
)


class TestAIExceptions:
    def test_ai_error_base(self):
        with pytest.raises(AIError):
            raise AIError("Test error")
    
    def test_ai_api_error_with_status(self):
        error = AIAPIError("API call failed", status_code=500)
        assert error.status_code == 500
        assert str(error) == "API call failed"
    
    def test_ai_rate_limit_error(self):
        error = AIRateLimitError("Rate limit exceeded", retry_after=60)
        assert error.retry_after == 60
    
    def test_exception_hierarchy(self):
        assert issubclass(AIAPIError, AIError)
        assert issubclass(AITimeoutError, AIError)
        assert issubclass(AIRateLimitError, AIError)
        assert issubclass(AIValidationError, AIError)
        assert issubclass(AIImageError, AIError)


class TestImageFormat:
    def test_image_format_values(self):
        assert ImageFormat.PNG.value == "png"
        assert ImageFormat.JPG.value == "jpg"
        assert ImageFormat.JPEG.value == "jpeg"
    
    def test_image_format_members(self):
        assert "png" in [f.value for f in ImageFormat]
        assert "jpg" in [f.value for f in ImageFormat]
        assert "jpeg" in [f.value for f in ImageFormat]


class TestChartViolationType:
    def test_violation_types(self):
        assert ChartViolationType.EXCURSION.value == "excursion"
        assert ChartViolationType.GAP.value == "gap"
        assert ChartViolationType.SLOW_RECOVERY.value == "slow_recovery"
        assert ChartViolationType.FREQUENT_ACCESS.value == "frequent_access"


class TestModelArkClientStaticMethods:
    def test_parse_json_response_valid(self):
        valid_json = '{"key": "value", "number": 42}'
        result = ModelArkClient.parse_json_response(valid_json)
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_parse_json_response_with_code_block(self):
        text_with_json = '''Here's the result:
```json
{"test": "data", "items": [1, 2, 3]}
```
'''
        result = ModelArkClient.parse_json_response(text_with_json)
        assert result["test"] == "data"
        assert result["items"] == [1, 2, 3]
    
    def test_parse_json_response_empty(self):
        result = ModelArkClient.parse_json_response("")
        assert result == {}
    
    def test_parse_json_response_invalid(self):
        result = ModelArkClient.parse_json_response("not valid json")
        assert result == {}
    
    def test_safe_parse_datetime_valid(self):
        dt = ModelArkClient.safe_parse_datetime("2026-05-14T14:00:00")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 5
        assert dt.day == 14
    
    def test_safe_parse_datetime_with_space(self):
        dt = ModelArkClient.safe_parse_datetime("2026-05-14 14:00:00")
        assert dt is not None
        assert dt.hour == 14
    
    def test_safe_parse_datetime_with_z(self):
        dt = ModelArkClient.safe_parse_datetime("2026-05-14T14:00:00Z")
        assert dt is not None
    
    def test_safe_parse_datetime_invalid(self):
        dt = ModelArkClient.safe_parse_datetime("not a date")
        assert dt is None
    
    def test_safe_parse_datetime_none(self):
        dt = ModelArkClient.safe_parse_datetime(None)
        assert dt is None
    
    def test_encode_image_to_base64(self):
        test_bytes = b"test image data"
        import base64
        expected = base64.b64encode(test_bytes).decode('utf-8')
        result = ModelArkClient.encode_image_to_base64(test_bytes)
        assert result == expected
    
    def test_detect_image_format_png(self):
        result = ModelArkClient.detect_image_format("test.PNG")
        assert result == ImageFormat.PNG
    
    def test_detect_image_format_jpg(self):
        result = ModelArkClient.detect_image_format("test.jpg")
        assert result == ImageFormat.JPG
    
    def test_detect_image_format_jpeg(self):
        result = ModelArkClient.detect_image_format("test.JPEG")
        assert result == ImageFormat.JPG
    
    def test_detect_image_format_unknown(self):
        result = ModelArkClient.detect_image_format("test.gif")
        assert result is None
    
    def test_validate_image_size_small(self):
        small_image = b"x" * (1 * 1024 * 1024)
        assert ModelArkClient.validate_image_size(small_image, max_size_mb=10) == True
    
    def test_validate_image_size_large(self):
        large_image = b"x" * (15 * 1024 * 1024)
        assert ModelArkClient.validate_image_size(large_image, max_size_mb=10) == False


class TestModelArkClient:
    def test_init_defaults(self):
        with patch('app.config.settings', new=MagicMock()):
            client = ModelArkClient(
                base_url="https://test.api/v3",
                api_key="test-key"
            )
            assert client.base_url == "https://test.api/v3"
            assert client.api_key == "test-key"
    
    def test_init_with_timeout(self):
        client = ModelArkClient(
            base_url="https://test.api/v3",
            api_key="test-key",
            timeout=30,
            max_retries=2
        )
        assert client.timeout == 30
        assert client.max_retries == 2
    
    def test_extract_response_content(self):
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"result": "success"}'
                    }
                }
            ]
        }
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            client = object.__new__(ModelArkClient)
            client._client = None
            
            content = client._extract_response_content(mock_response)
            assert content == '{"result": "success"}'
    
    def test_extract_response_content_empty_choices(self):
        mock_response = {
            "choices": []
        }
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            client = object.__new__(ModelArkClient)
            client._client = None
            
            content = client._extract_response_content(mock_response)
            assert content == '{}'
    
    def test_extract_response_content_no_message(self):
        mock_response = {
            "choices": [{}]
        }
        
        with patch.object(ModelArkClient, '__init__', return_value=None):
            client = object.__new__(ModelArkClient)
            client._client = None
            
            content = client._extract_response_content(mock_response)
            assert content == '{}'


class TestClientResponseParsing:
    def test_extract_json_from_text_with_code_block(self):
        from app.ai.client import ModelArkClient
        
        text = '''Some text here
```json
{
  "test": "value",
  "nested": {"key": "data"}
}
```
More text'''
        
        result = ModelArkClient._extract_json_from_text(text)
        assert result["test"] == "value"
        assert result["nested"]["key"] == "data"
    
    def test_extract_json_from_text_multiple_code_blocks(self):
        from app.ai.client import ModelArkClient
        
        text = '''First:
```json
{"first": true}
```
Second:
```json
{"second": true}
```'''
        
        result = ModelArkClient._extract_json_from_text(text)
        assert result["first"] == True
    
    def test_extract_json_from_text_plain_json(self):
        from app.ai.client import ModelArkClient
        
        text = '{"direct": "json"}'
        
        result = ModelArkClient._extract_json_from_text(text)
        assert result["direct"] == "json"
