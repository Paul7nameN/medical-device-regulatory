from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from httpx import Timeout
import asyncio
import json
import re
import base64
import logging

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from app.config import settings

logger = logging.getLogger(__name__)


class AIError(Exception):
    pass


class AIAPIError(AIError):
    def __init__(self, message: str, status_code: int = 500):
        self.status_code = status_code
        super().__init__(message)


class AITimeoutError(AIError):
    pass


class AIRateLimitError(AIError):
    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message)


class AIValidationError(AIError):
    pass


class AIImageError(AIError):
    pass


class ImageFormat(str, Enum):
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"


class ChartViolationType(str, Enum):
    EXCURSION = "excursion"
    GAP = "gap"
    SLOW_RECOVERY = "slow_recovery"
    FREQUENT_ACCESS = "frequent_access"


class ModelArkClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        self.base_url = base_url or settings.modelark_base_url
        self.api_key = api_key or settings.modelark_api_key
        self.timeout = timeout if timeout is not None else settings.modelark_timeout
        self.max_retries = max_retries if max_retries is not None else settings.modelark_max_retries
        self.model_chart = settings.model_chart_analysis
        self.model_text = settings.model_text_analysis
        self._client = None
        
        logger.info(
            "ModelArkClient initialized",
            extra={
                "base_url": self.base_url,
                "timeout": self.timeout,
                "max_retries": self.max_retries,
                "has_api_key": bool(self.api_key)
            }
        )
    
    @property
    def client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=Timeout(timeout=self.timeout)
                )
                logger.debug("OpenAI client created successfully")
            except ImportError:
                logger.error("openai package not installed")
                raise AIError("openai package not installed. Run 'pip install openai'")
        return self._client
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        response_format: Optional[Dict] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            logger.error("ModelArk API key not configured")
            raise AIValidationError("ModelArk API key not configured. Set MODELARK_API_KEY environment variable.")
        
        start_time = datetime.now()
        
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        
        request_log = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "has_response_format": bool(response_format)
        }
        
        logger.debug(
            "Sending chat completion request",
            extra={"request": request_log}
        )
        
        try:
            for attempt in range(self.max_retries):
                try:
                    request_kwargs = {**kwargs, "messages": messages}
                    response = await self.client.chat.completions.create(**request_kwargs)
                    result = response.model_dump()
                    
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    usage = result.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
                    
                    logger.info(
                        "Chat completion successful",
                        extra={
                            "model": model,
                            "duration_seconds": duration,
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        logger.error(
                            f"API call failed after {self.max_retries} attempts",
                            extra={
                                "error": str(e),
                                "model": model
                            }
                        )
                        raise AIAPIError(f"API call failed after {self.max_retries} attempts: {str(e)}")
                    
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(
                        f"API attempt {attempt + 1} failed, retrying in {wait_time}s",
                        extra={
                            "error": str(e),
                            "retry_count": attempt + 1,
                            "wait_time": wait_time
                        }
                    )
                    await asyncio.sleep(wait_time)
            
            logger.error("All retries exhausted")
            raise AIAPIError(f"API call failed after {self.max_retries} attempts")
            
        except RetryError as e:
            logger.error("Retry error occurred", extra={"error": str(e)})
            raise AIAPIError(f"All retries failed: {str(e)}")
    
    async def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        image_format: ImageFormat = ImageFormat.PNG
    ) -> Dict[str, Any]:
        format_str = image_format.value
        if format_str == "jpeg":
            format_str = "jpg"
        
        logger.info(
            "Starting image analysis",
            extra={
                "format": format_str,
                "model": self.model_chart
            }
        )
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{format_str};base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        return await self.chat_completion(
            messages=messages,
            model=self.model_chart,
            response_format={"type": "json_object"}
        )
    
    async def analyze_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(
            "Starting text analysis",
            extra={
                "has_system_prompt": bool(system_prompt),
                "model": self.model_text
            }
        )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat_completion(
            messages=messages,
            model=self.model_text,
            response_format={"type": "json_object"}
        )
    
    @staticmethod
    def parse_json_response(content: str) -> Dict[str, Any]:
        try:
            result = json.loads(content)
            logger.debug("JSON parsed successfully")
            return result
        except json.JSONDecodeError:
            logger.debug("Direct JSON parse failed, trying text extraction")
            return ModelArkClient._extract_json_from_text(content)
    
    @staticmethod
    def _extract_response_content(response: Dict[str, Any]) -> str:
        try:
            choices = response.get("choices", [])
            if not choices:
                return '{}'
            first_choice = choices[0]
            message = first_choice.get("message", {})
            content = message.get("content")
            return content if content is not None else '{}'
        except Exception:
            return '{}'
    
    @staticmethod
    def _extract_json_from_text(text: str) -> Dict[str, Any]:
        code_block_pattern = r'```json\s*([\s\S]*?)\s*```'
        code_block_matches = re.findall(code_block_pattern, text)
        for json_content in code_block_matches:
            try:
                result = json.loads(json_content)
                logger.debug("JSON extracted from code block successfully")
                return result
            except json.JSONDecodeError:
                continue
        
        def find_complete_json(s: str, start_pos: int = 0) -> Optional[str]:
            first_brace = s.find('{', start_pos)
            if first_brace == -1:
                return None
            
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i in range(first_brace, len(s)):
                char = s[i]
                
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                
                if char == '"':
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return s[first_brace:i+1]
            
            return None
        
        pos = 0
        while pos < len(text):
            json_str = find_complete_json(text, pos)
            if json_str:
                try:
                    result = json.loads(json_str)
                    logger.debug("JSON extracted from text successfully")
                    return result
                except json.JSONDecodeError:
                    pos = text.find(json_str, pos) + len(json_str) if json_str else pos + 1
            else:
                break
        
        logger.warning("No valid JSON found in response")
        return {}
    
    @staticmethod
    def safe_parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                result = datetime.strptime(dt_str.rstrip('Z').rstrip('+00:00'), fmt)
                return result
            except (ValueError, TypeError):
                continue
        
        try:
            result = datetime.fromisoformat(dt_str)
            return result
        except (ValueError, TypeError):
            logger.warning(f"Could not parse datetime: {dt_str[:20] if dt_str else 'None'}")
            return None
    
    @staticmethod
    def encode_image_to_base64(image_bytes: bytes) -> str:
        result = base64.b64encode(image_bytes).decode('utf-8')
        logger.debug(
            "Image encoded to base64",
            extra={"size_bytes": len(image_bytes), "base64_length": len(result)}
        )
        return result
    
    @staticmethod
    def detect_image_format(filename: str) -> Optional[ImageFormat]:
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.png'):
            logger.debug(f"Detected PNG format for: {filename}")
            return ImageFormat.PNG
        elif filename_lower.endswith('.jpg') or filename_lower.endswith('.jpeg'):
            logger.debug(f"Detected JPG format for: {filename}")
            return ImageFormat.JPG
        
        logger.warning(f"Unsupported image format for: {filename}")
        return None
    
    @staticmethod
    def validate_image_size(image_bytes: bytes, max_size_mb: int = 10) -> bool:
        size_mb = len(image_bytes) / (1024 * 1024)
        is_valid = size_mb <= max_size_mb
        
        if not is_valid:
            logger.warning(
                f"Image exceeds size limit: {size_mb:.2f}MB > {max_size_mb}MB"
            )
        else:
            logger.debug(f"Image size valid: {size_mb:.2f}MB")
        
        return is_valid
