# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

Full-stack San Jose Sharks fan platform. FastAPI backend (Python 3.13) + Next.js 15 frontend (Pages Router). Aggregates NHL game data, YouTube highlights, AI-generated recaps (Claude), and Reddit sentiment for every Sharks game.

## Commands

### Local stack (Docker — preferred)
```bash
docker compose up -d --build              # Start postgres + redis + backend + frontend
docker exec nhl-backend alembic upgrade head   # Apply DB migrations
docker compose logs -f backend            # Tail logs
```
Frontend at `localhost:3000`, backend at `localhost:8000`, OpenAPI docs at `/docs`.

### Backend (host, with `backend/venv`)
```bash
cd backend
uvicorn app.main:app --reload             # Dev server (also runs APScheduler on startup)
alembic revision -m "description"         # Create migration
alembic upgrade head                      # Apply migrations
pytest tests/ -v                          # Run all tests
pytest tests/test_health.py::test_name    # Run a single test
pytest -m unit                            # Run by marker (unit | integration | slow)
```

### Frontend
```bash
cd frontend
npm run dev    # next dev
npm run build  # next build
npm run lint   # next lint (eslint)
```

### Pre-commit
`./pre-commit-check.sh` scans staged diff for `AIzaSy…`, `sk-ant-…`, `sk-proj-…` keys and ensures `.env` is gitignored. Run before any commit.

## Architecture

### Data flow — staged game processing
1. **Schedule sync** (`app/scripts/fetch_season.py` via `update_game_scores_job`): hourly pull of the Sharks season from the NHL Stats API; upserts `Game` rows.
2. **Video fetch** (`check_and_fetch_videos_job`, hourly :05): for `Game.status in ("FINAL","OFF")` rows where `highlights_fetched`/`professor_hockey_fetched` are false, calls `services.youtube.search_game_highlights` and inserts `Video` rows. The two channels (NHL official, Professor Hockey) are tracked independently via separate boolean flags so a YouTube quota exhaustion on one doesn't strand the other.
3. **Basic stats** (`fetch_basic_stats_job`, hourly :10): `process_game_immediate()` pulls boxscore JSON, populates scorers/scores, sets `basic_stats_fetched=True`.
4. **Reddit sentiment** (`fetch_reddit_sentiment_job`, hourly :15): scrapes the r/SanJoseSharks game thread, sends comments to Claude (`services.sentiment.analyze_game_sentiment`), writes JSON blob to `Game.reddit_sentiment`. Capped at 5 games/run to control Claude spend.

The processing-state booleans on `Game` (`basic_stats_fetched`, `reddit_fetched`, `highlights_fetched`, `professor_hockey_fetched`, `quotes_fetched`) are the contract between jobs — `crud/game.py` exposes `get_games_needing_*` queries that drive each job. When adding a new processing stage, add a flag + `mark_*_fetched` helper rather than overloading existing ones.

### YouTube quota handling
`services.youtube.YouTubeQuotaExceeded` is raised when the Data API v3 quota is hit. Jobs catch this, set a local `quota_exceeded` flag, and skip remaining work for that run — they do *not* mark games as fetched, so the next run retries. Preserve this pattern when touching the video pipeline.

### Backend layout
- `app/main.py` — FastAPI app, Sentry init, response-time middleware, CORS, lifespan that boots/shuts the scheduler.
- `app/api/v1/routers/` — Route modules mounted under `/api/<name>` in `main.py`. Adding an endpoint = new router file + `app.include_router(...)` line.
- `app/services/` — External integrations (`nhl.py`, `youtube.py`, `claude.py`, `reddit.py`, `sentiment.py`) and `redis_cache.py`. Routers and jobs depend on services; services do not import routers.
- `app/crud/` — All SQLAlchemy queries live here, one module per primary entity. Routers/jobs go through CRUD, not raw queries.
- `app/jobs/` — APScheduler jobs (`scheduler.py` is the registry) + `game_processor.py` for per-game pipelines.
- `app/models/` — SQLAlchemy ORM models. Schema changes require an Alembic migration in `backend/alembic/versions/`.
- `app/auth/clerk.py` — Bearer-token verification against Clerk for authenticated comment routes.
- `app/scripts/` — One-shot CLIs (e.g., `fetch_season.py`, `reset_and_fetch.py`) — also imported by jobs.

### Caching
`services.redis_cache.cache` is a singleton. `REDIS_ENABLED=false` (the default outside Docker) makes it a no-op — code can call `cache.get/set` unconditionally. Cache hit/miss/invalidation counters are exposed via `/api/monitoring`.

### Frontend
Next.js **Pages Router** (not App Router) under `frontend/pages/`. `lib/posthog.ts` and `sentry.*.config.ts` wire analytics/error tracking. API base URL comes from `NEXT_PUBLIC_API_URL`.

### Deployment
- Local: `docker-compose.yml` (postgres + redis + backend + frontend on `nhl-network`).
- Production: Railway. The **root `Dockerfile`** is the Railway build — it copies `backend/` and runs `start.sh` (which runs `alembic upgrade head` then `uvicorn`). The separate `backend/Dockerfile` is for `docker compose`. Keep them in sync when touching Python deps or startup.

## Configuration

Settings load from `.env` via `pydantic-settings` (`app/config.py`). Required: `DATABASE_URL`. Feature-gated: `YOUTUBE_API_KEY`, `CLAUDE_API_KEY`, `CLERK_SECRET_KEY`, `SENTRY_DSN`, `REDIS_*`. Missing optional keys silently disable the corresponding feature — don't add fail-fast checks for them.

Scheduler timezone is `America/Los_Angeles` (`settings.TIMEZONE`). All hourly cron jobs are PT-anchored.
