from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # External APIs
    YOUTUBE_API_KEY: str | None = None
    CLAUDE_API_KEY: str | None = None
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

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

    # prospect-service (Go gRPC microservice). Optional, house pattern: when
    # unset the prospects endpoints soft-fail to empty rather than erroring.
    # In docker compose this is set to "prospect-service:50051".
    PROSPECT_SERVICE_ADDR: str | None = None
    # Per-call deadline (seconds) for gRPC calls to the prospect-service, so a
    # hung service can't tie up FastAPI's threadpool.
    PROSPECT_SERVICE_TIMEOUT: float = 2.0

    # Sentry Error Tracking
    SENTRY_DSN: str | None = None

    # Redis Cache
    REDIS_ENABLED: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # Reddit (PRAW script app — credentials are required to fetch real data;
    # missing values cause discovery and analysis to no-op silently.)
    REDDIT_CLIENT_ID: str | None = None
    REDDIT_CLIENT_SECRET: str | None = None
    REDDIT_USERNAME: str | None = None
    REDDIT_PASSWORD: str | None = None
    REDDIT_USER_AGENT: str = "python:nhl-fan-insights:1.0 (by /u/unknown)"
    REDDIT_SUBREDDIT: str = "SanJoseSharks"
    # Bridging mode: when True, use the public reddit.com/.json endpoints
    # (no auth, ~10 req/min limit). When False (default), use PRAW with the
    # credentials above. Flip back to False the day API access is approved.
    REDDIT_USE_ANON: bool = False

    class Config:
        # env_file and encoding for reading .env automatically
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
