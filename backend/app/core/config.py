from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized app configuration, loaded from environment variables / .env.

    WHY: hardcoding secrets or DB URLs in code is a security risk and makes
    deployment painful (different values per environment: local, staging, prod).
    Pydantic validates types and fails fast at startup if something required
    is missing, instead of failing later with a confusing runtime error.
    """

    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:5173"
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg2://", 1)
            if v.startswith("postgresql://") and not v.startswith("postgresql+psycopg2://"):
                return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        origins = []
        for o in self.CORS_ORIGINS.split(","):
            cleaned = o.strip()
            if cleaned:
                origins.append(cleaned.rstrip("/"))
                origins.append(cleaned.rstrip("/") + "/")
        return list(dict.fromkeys(origins))


settings = Settings()
