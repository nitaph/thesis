from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Core
    DATABASE_URL: str
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"          # set your default
    LLM_TEMPERATURE: float = 0.8
    LLM_TOP_P: float = 1.0
    LLM_MAX_TOKENS: int = 800
    LLM_SEED: int | None = None

    # Infra
    REDIS_URL: str | None = None
    CACHE_TTL_S: int = 60 * 60              # 1 hour
    TIMEOUT_S: int = 25

    # Tasks config
    TASKS_STYLE_A: int = 2                   # 2–3
    TASKS_STYLE_B: int = 2

    # Governance
    LOG_PROMPT_VERSION: str = "v1"
    STRIP_PII: bool = True

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
