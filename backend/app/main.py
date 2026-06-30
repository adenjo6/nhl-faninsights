from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.api.v1.routers import recap, games, comments, prospects, reddit, monitoring
from app.jobs.scheduler import start_scheduler, shutdown_scheduler
from app.db.session import SessionLocal
from app.config import settings
from app.services.redis_cache import cache
from app.services.prospect_client import prospect_client
import logging
import time
import collections
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry (if DSN configured)
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )
    logger.info("✓ Sentry error tracking initialized")


# Response time tracking
response_time_stats = collections.defaultdict(lambda: {"count": 0, "total_ms": 0.0, "max_ms": 0.0})


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to track and log response times."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # Add header
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        # Track stats per endpoint
        path = request.url.path
        stats = response_time_stats[path]
        stats["count"] += 1
        stats["total_ms"] += duration_ms
        stats["max_ms"] = max(stats["max_ms"], duration_ms)

        # Log slow requests
        if duration_ms > 200:
            logger.warning(f"Slow request: {request.method} {path} took {duration_ms:.0f}ms")

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting Sharks Fan Hub API...")
    start_scheduler()
    logger.info("✓ Scheduler started")
    prospect_client.connect()

    yield

    # Shutdown
    logger.info("Shutting down Sharks Fan Hub API...")
    shutdown_scheduler()
    logger.info("✓ Scheduler stopped")
    prospect_client.close()


app = FastAPI(
    title="Sharks Fan Hub API",
    description="San Jose Sharks fan platform with game recaps, stats, and more",
    version="0.1.0",
    lifespan=lifespan
)

# Response time tracking middleware (must be added before CORS)
app.add_middleware(ResponseTimeMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recap.router, prefix="/api/recap", tags=["recap"])
app.include_router(games.router, prefix="/api/games", tags=["games"])
app.include_router(comments.router, prefix="/api/comments", tags=["comments"])
app.include_router(prospects.router, prefix="/api/prospects", tags=["prospects"])
app.include_router(reddit.router, prefix="/api/reddit", tags=["reddit"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])


@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Sharks Fan Hub API",
        "version": "0.1.0"
    }


@app.get("/health")
def health_check():
    """Detailed health check with database and cache connectivity test."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "nhl-fan-insights-backend",
        "version": "0.1.0",
        "scheduler": "running",
        "database": "unknown",
        "cache": "unknown"
    }

    # Test database connectivity
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"disconnected: {str(e)}"

    # Test Redis cache
    redis_health = cache.health_check()
    health_status["cache"] = redis_health.get("status", "unknown")

    return health_status


@app.get("/ready")
def readiness_check():
    """Kubernetes-style readiness probe."""
    return {"ready": True}


@app.get("/api/monitoring/response-times")
def get_response_times():
    """Per-endpoint response time statistics."""
    endpoints = []
    for path, stats in sorted(response_time_stats.items()):
        if stats["count"] > 0:
            endpoints.append({
                "path": path,
                "count": stats["count"],
                "avg_ms": round(stats["total_ms"] / stats["count"], 1),
                "max_ms": round(stats["max_ms"], 1),
            })
    return {"endpoints": endpoints}