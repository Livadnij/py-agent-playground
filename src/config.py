from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_TIMEOUT: int
    LLM_ALLOWED_DIRECTORIES: list[str]

    LLM_SUMMARY_THRESHOLD_PERCENT: int = 75
    LLM_SUMMARY_MAX_TOKENS: int = 2000
    LLM_SUMMARY_TEMPERATURE: float = 0.2

    LLM_COMPLETION_TEMPERATURE: float = 0.7

    LLM_MAX_TOOL_ROUNDS: int = 10
    LLM_MAX_IDENTICAL_CALLS: int = 3

    LLM_MAX_FILE_SIZE: int = 8192

    PRODUCTION: bool
  
settings = Settings()	  