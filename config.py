# config.py

from pydantic import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    WEATHER_API_KEY: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
