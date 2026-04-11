from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Application Tracker"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/app.db"
    storage_backend: str = "local"
    local_storage_path: str = "./data/artefacts"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

