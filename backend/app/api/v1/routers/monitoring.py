"""
Monitoring and metrics endpoints for debugging and observability.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
from datetime import datetime
import psutil
import logging

from app.api.v1.deps import get_db
from app.services.redis_cache import cache
from app.models.game import Game
from app.models.video import Video

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/metrics", response_model=Dict[str, Any])
def get_metrics():
    """
    Get comprehensive system and application metrics.

    Returns:
        - Cache performance (hit rate, miss rate, invalidations)
        - System resources (CPU, memory, disk)
        - Application statistics
    """
    # Get cache metrics
    cache_stats = cache.get_metrics()

    # Get system metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        system_stats = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used / (1024 * 1024),
            "memory_total_mb": memory.total / (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024 * 1024 * 1024),
            "disk_total_gb": disk.total / (1024 * 1024 * 1024)
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        system_stats = {"error": str(e)}

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cache": cache_stats,
        "system": system_stats,
        "service": "nhl-fan-insights-backend",
        "version": "0.1.0"
    }


@router.get("/cache/stats", response_model=Dict[str, Any])
def get_cache_stats():
    """
    Get detailed cache statistics.

    Returns detailed information about cache performance:
    - Hit/miss rates
    - Invalidation count
    - Error count
    - Connection status
    """
    return cache.get_metrics()


@router.post("/cache/reset")
def reset_cache_metrics():
    """
    Reset cache metrics counters.

    This resets hit/miss/invalidation counters but does not clear cached data.
    """
    cache.reset_metrics()
    return {
        "message": "Cache metrics reset successfully",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/cache/health")
def cache_health():
    """
    Check Redis cache health status.

    Returns connection status and configuration.
    """
    return cache.health_check()


@router.get("/database/stats")
def get_database_stats(db: Session = Depends(get_db)):
    """
    Get database statistics.

    Returns:
        - Table row counts
        - Database size
        - Connection info
    """
    try:
        # Get table row counts
        game_count = db.query(Game).count()
        video_count = db.query(Video).count()
        completed_games = db.query(Game).filter(Game.status.in_(['FINAL', 'OFF'])).count()
        games_with_videos = db.query(Game).filter(Game.videos_fetched == True).count()

        # Get database size
        result = db.execute(text("SELECT pg_database_size(current_database()) as size"))
        db_size_bytes = result.scalar()
        db_size_mb = db_size_bytes / (1024 * 1024) if db_size_bytes else 0

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "tables": {
                "games": {
                    "total": game_count,
                    "completed": completed_games,
                    "with_videos": games_with_videos,
                    "pending_videos": completed_games - games_with_videos
                },
                "videos": {
                    "total": video_count
                }
            },
            "database": {
                "size_mb": round(db_size_mb, 2),
                "status": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/logs/recent")
def get_recent_logs():
    """
    Get recent application logs (if log file exists).

    Returns the last 100 lines of application logs.
    """
    try:
        # This would read from a log file if configured
        # For now, return a placeholder
        return {
            "message": "Log endpoint - implement log file reading if needed",
            "suggestion": "Use Docker logs or centralized logging (e.g., CloudWatch, Datadog)"
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check for all system components.

    Checks:
    - Database connectivity
    - Redis cache
    - Disk space
    - Memory usage
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Connected"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }

    # Check Redis
    redis_health = cache.health_check()
    health_status["components"]["cache"] = redis_health

    # Check system resources
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Warn if memory > 90% or disk > 85%
        resource_status = "healthy"
        warnings = []

        if memory.percent > 90:
            resource_status = "warning"
            warnings.append(f"High memory usage: {memory.percent}%")

        if disk.percent > 85:
            resource_status = "warning"
            warnings.append(f"High disk usage: {disk.percent}%")

        health_status["components"]["system_resources"] = {
            "status": resource_status,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "warnings": warnings
        }

        if warnings:
            health_status["status"] = "degraded"

    except Exception as e:
        health_status["components"]["system_resources"] = {
            "status": "unknown",
            "message": str(e)
        }

    return health_status
