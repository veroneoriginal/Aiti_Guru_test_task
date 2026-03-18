# app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # База данных
    DATABASE_URL: str

    # Банк
    BANK_API_URL: str
    BANK_API_TIMEOUT: int = 10  # секунды

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
