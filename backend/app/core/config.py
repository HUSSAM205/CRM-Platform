from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CRM Platform API"
    environment: str = "development"
    debug: bool = True

    database_url: str = "postgresql+psycopg://user:password@localhost:5432/crm"

    jwt_secret: str = "dev-only-change-me"
    refresh_secret: str = "dev-only-change-me-too"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    cors_origins: list[str] = ["http://localhost:3000"]

    storage_backend: str = "local"
    local_storage_path: str = "./data/uploads"
    s3_endpoint_url: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket: str | None = None

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
