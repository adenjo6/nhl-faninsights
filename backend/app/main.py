from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.api.v1.routers import recap, games, comments, prospects, reddit, monitoring
from app.scheduler import start_scheduler, shutdown_scheduler
from app.db.session import SessionLocal
from app.config import settings
from app.services.redis_cache import cache
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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

    yield

    # Shutdown
    logger.info("Shutting down Sharks Fan Hub API...")
    shutdown_scheduler()
    logger.info("✓ Scheduler stopped")


app = FastAPI(
    title="Sharks Fan Hub API",
    description="San Jose Sharks fan platform with game recaps, stats, and more",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recap.router, prefix="/recap", tags=["recap"])
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