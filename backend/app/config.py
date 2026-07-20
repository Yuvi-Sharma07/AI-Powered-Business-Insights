from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    database_url: str = "sqlite:///./analytics.db"
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    llm_provider: str = "gemini"  # 'gemini' or 'openai'
    port: int = 8000
    host: str = "0.0.0.0"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
