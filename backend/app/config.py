from typing import Any, Optional, List
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MED-THERM Compliance Engine"
    app_version: str = "0.1.0"
    debug: bool = True

    cors_origins: List[str] = ["*"]

    database_url: str
    database_url_async: str

    vllm_provider: Optional[str] = None
    vllm_api_key: Optional[str] = None
    vllm_model: Optional[str] = None

    modelark_base_url: str
    modelark_api_key: Optional[str] = None

    model_chart_analysis: str
    model_text_analysis: str

    modelark_timeout: int = 60
    modelark_max_retries: int = 3
    modelark_retry_delay: float = 1.0

    ai_enabled: bool = False

    @field_validator("ai_enabled", mode="before")
    @classmethod
    def parse_ai_enabled(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip().lower()
            if v in ("", "0", "false", "no", "off", "none"):
                return False
            if v in ("1", "true", "yes", "on"):
                return True
        return v

    @field_validator("modelark_api_key", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

if settings.modelark_api_key is not None and not settings.ai_enabled:
    settings.ai_enabled = True
