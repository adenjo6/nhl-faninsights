from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # External APIs
    YOUTUBE_API_KEY: str | None = None
    CLAUDE_API_KEY: str | None = None

    # Clerk Auth
    CLERK_SECRET_KEY: str | None = None
    CLERK_WEBHOOK_SECRET: str | None = None

    # Application settings
    SHARKS_TEAM_ID: str = "SJS"
    BARRACUDA_TEAM_ID: str = "SJB"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:3000"

    # Scheduler timezone
    TIMEZONE: str = "America/Los_Angeles"

    # Redis Cache
    REDIS_ENABLED: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    class Config:
        # env_file and encoding for reading .env automatically
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
