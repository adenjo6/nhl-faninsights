# NHL Fan Insights

Full-stack web application for San Jose Sharks game tracking with automated video highlights, AI-generated recaps, and fan discussion.

## Overview

Automated platform that fetches and displays San Jose Sharks game information including:
- NHL official video highlights
- Professor Hockey game analysis videos
- AI-generated game recaps
- Fan comments and discussion threads
- Reddit game thread integration
- Player statistics and milestones

## Tech Stack

### Backend
- Python 3.13
- FastAPI 0.116.1
- PostgreSQL 15 with SQLAlchemy 2.0
- Redis 7 (caching)
- APScheduler (background jobs)
- Alembic (database migrations)

### Frontend
- Next.js 15
- TypeScript
- React
- TailwindCSS

### DevOps
- Docker with multi-stage builds
- GitHub Actions CI/CD
- Railway deployment
- Automated testing with pytest

### External APIs
- NHL Stats API (game data)
- YouTube Data API v3 (video search)
- Anthropic Claude API (AI recaps)
- Reddit API (game threads)

## Quick Start

### Local Development with Docker

```bash
# 1. Clone repository
git clone https://github.com/adenjo6/nhl-faninsights.git
cd nhl-faninsights

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your YOUTUBE_API_KEY

# 3. Start all services
docker compose up -d --build

# 4. Run database migrations
docker exec nhl-backend alembic upgrade head

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Deploy to Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

Quick deploy with Railway:
```bash
./deploy-railway.sh
```

## Project Structure

```
nhl-faninsights/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── crud/             # Database operations
│   │   ├── services/         # External API integrations
│   │   ├── jobs/             # Background tasks
│   │   └── db/               # Database configuration
│   ├── alembic/              # Database migrations
│   ├── tests/                # Test suite
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── pages/                # Next.js pages
│   ├── lib/                  # Utilities
│   ├── styles/               # CSS
│   ├── Dockerfile
│   └── package.json
│
├── .github/
│   └── workflows/            # CI/CD pipelines
│
└── docker-compose.yml        # Local development stack
```

## Features

### Automated Game Processing
- Hourly scheduler checks for new Sharks games
- Automatic video fetching from YouTube
- AI-powered game recap generation
- Reddit game thread integration
- Staged processing pipeline (immediate, 2hr, 4hr, 12hr, 24hr)

### Performance
- Redis caching for API responses
- Database indexes for 60% query performance improvement
- Multi-stage Docker builds for optimized images
- Health checks and automatic restarts

### User Features
- Authenticated comment system
- Threaded replies
- Game video highlights
- Player statistics and milestones
- Prospects directory

## Environment Variables

### Required
```bash
YOUTUBE_API_KEY=your_youtube_api_key_here
DATABASE_URL=postgresql://user:pass@host:port/db
```

### Optional
```bash
CLAUDE_API_KEY=your_claude_api_key
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
ENVIRONMENT=production
```

See `.env.example` for complete list.

## Development

### Run Tests
```bash
# Backend tests
docker exec nhl-backend pytest tests/ -v

# Frontend linting
docker exec nhl-frontend npm run lint
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker logs nhl-backend --tail=50
```

### Database Migrations
```bash
# Create migration
docker exec nhl-backend alembic revision -m "description"

# Apply migrations
docker exec nhl-backend alembic upgrade head
```

## CI/CD Pipeline

GitHub Actions automatically:
1. Runs tests on pull requests
2. Builds Docker images
3. Deploys to production on merge to main

See `.github/workflows/` for pipeline configuration.

## API Documentation

Interactive API documentation available at:
- Local: http://localhost:8000/docs
- Production: https://your-backend.railway.app/docs

## Security

- API keys managed via environment variables
- Non-root Docker containers
- SQL injection protection via SQLAlchemy ORM
- Input validation with Pydantic
- Pre-commit security checks

Run security check before committing:
```bash
./pre-commit-check.sh
```

## Performance

- Average API response time: <100ms (cached)
- Database query optimization: 60% improvement with indexes
- Docker image size: 250MB (backend), 180MB (frontend)
- CI/CD pipeline: 5-10 minutes full deployment

## Deployment

### Railway (Recommended)
- PostgreSQL and Redis included
- Automatic SSL
- Health monitoring
- Cost: $0-5/month on free tier

### Manual Setup
1. Set up PostgreSQL and Redis
2. Configure environment variables
3. Run migrations
4. Deploy Docker containers

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Troubleshooting

### Common Issues

**Backend won't start:**
```bash
docker logs nhl-backend
# Check for missing YOUTUBE_API_KEY in .env
```

**Frontend can't connect:**
```bash
# Verify NEXT_PUBLIC_API_URL in frontend/.env.local
```

**Database errors:**
```bash
# Reset and re-run migrations
docker exec nhl-backend alembic downgrade base
docker exec nhl-backend alembic upgrade head
```

## Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [.github/workflows/README.md](.github/workflows/README.md) - CI/CD documentation
- [.github/SECURITY.md](.github/SECURITY.md) - Security policy

## Contributing

This is a personal project, but suggestions and bug reports are welcome via GitHub Issues.

## License

MIT License

## Credits

- NHL Stats API for game data
- YouTube Data API for video search
- Anthropic Claude for AI recaps
- Professor Hockey for analysis videos
- Reddit API for community discussions
