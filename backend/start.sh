#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
# Bind the platform-provided port when present (Railway/Render/Heroku inject
# $PORT and route their edge proxy to it); fall back to 8000 for local Docker.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
