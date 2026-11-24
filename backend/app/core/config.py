from typing import List, Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "LLMGuard – AI Evaluation & Safety Monitoring Platform"
    API_VERSION: str = "0.8.0"
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Google AI Studio (Gemini API) Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # DeepEval Evaluation Judge Settings
    EVALUATION_MODEL: str = "gemini-3.5-flash-lite"
    FAITHFULNESS_THRESHOLD: float = 0.7
    ANSWER_RELEVANCY_THRESHOLD: float = 0.7
    HALLUCINATION_THRESHOLD: float = 0.7

    # Guardrails AI Settings - Phase 4 & 7
    MAX_INPUT_LENGTH: int = 4000
    ENABLE_INPUT_GUARDRAILS: bool = True
    ENABLE_OUTPUT_GUARDRAILS: bool = True
    GUARDRAILS_DB_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "safety_logs.db"
    )

    # Langfuse Observability Settings - Phase 5 & 7
    # Canonical endpoint variable is LANGFUSE_BASE_URL (LANGFUSE_HOST is supported as backwards-compatible alias)
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"
    LANGFUSE_HOST: Optional[str] = None
    ENABLE_OBSERVABILITY: bool = True

    @property
    def canonical_langfuse_host(self) -> str:
        """Canonical Langfuse endpoint URL resolving LANGFUSE_BASE_URL and LANGFUSE_HOST."""
        return self.LANGFUSE_HOST or self.LANGFUSE_BASE_URL or "https://cloud.langfuse.com"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
