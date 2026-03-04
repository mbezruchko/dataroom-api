from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    POSTGRES_URL: str
    STORAGE_PATH: str = "./data/storage"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()

Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)