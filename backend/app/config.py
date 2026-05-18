from pydantic_settings import BaseSettings
from typing import Optional, List


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

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

if settings.modelark_api_key and not settings.ai_enabled:
    settings.ai_enabled = True
