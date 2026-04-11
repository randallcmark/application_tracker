from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_SESSION_SECRET = "dev-insecure-change-me"


class Settings(BaseSettings):
    app_name: str = "Application Tracker"
    app_env: str = "development"
    auth_mode: Literal["local", "oidc", "mixed", "proxy", "none"] = "local"
    session_secret_key: str = DEVELOPMENT_SESSION_SECRET
    session_cookie_name: str = "ats_session"
    session_expire_days: int = 14
    csrf_cookie_name: str = "ats_csrf"
    csrf_expire_seconds: int = 2 * 60 * 60
    public_base_url: AnyHttpUrl = "http://localhost:8000"
    trusted_proxy_auth: bool = False
    database_url: str = "sqlite:///./data/app.db"
    storage_backend: str = "local"
    local_storage_path: str = "./data/artefacts"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("app_env", "auth_mode")
    @classmethod
    def normalize_lowercase(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_runtime_guardrails(self) -> "Settings":
        if self.app_env != "production":
            return self

        if self.auth_mode == "none":
            raise ValueError("AUTH_MODE=none is not allowed in production")

        if self.session_secret_key == DEVELOPMENT_SESSION_SECRET:
            raise ValueError("SESSION_SECRET_KEY must be changed in production")

        if self.public_base_url.scheme != "https":
            raise ValueError("PUBLIC_BASE_URL must use https in production")

        if self.auth_mode == "proxy" and not self.trusted_proxy_auth:
            raise ValueError("TRUSTED_PROXY_AUTH=true is required when AUTH_MODE=proxy")

        return self

    @property
    def session_cookie_secure(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
