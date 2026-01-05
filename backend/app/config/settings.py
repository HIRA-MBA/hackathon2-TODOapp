from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str

    # Authentication
    better_auth_secret: str
    better_auth_url: str = "http://localhost:3000"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Environment
    environment: str = "development"

    # OpenAI (Phase 3: AI Chatbot)
    openai_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def jwks_url(self) -> str:
        """URL to fetch JWKS from Better Auth."""
        return f"{self.better_auth_url}/api/auth/jwks"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
