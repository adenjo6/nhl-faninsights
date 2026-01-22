# Deployment Guide - Railway

This guide walks you through deploying NHL Fan Insights to Railway.

## Prerequisites

✅ Railway CLI installed (`railway version`: 4.25.1)
✅ Logged in to Railway (adenjo@ucsb.edu)
✅ Docker images working locally
✅ Environment variables ready

## Quick Deploy (5 minutes)

### Step 1: Initialize Railway Project
```bash
cd /Users/adenj/dev/projects/NhlFanInsights
railway init
```

**What happens:**
- Creates new project on Railway dashboard
- Links your local repo to Railway
- Generates project ID

**Choose:**
- Project name: `nhl-fan-insights`
- Start from: `Empty Project`

---

### Step 2: Add PostgreSQL Database
```bash
railway add --plugin postgresql
```

**What happens:**
- Creates PostgreSQL 15 database
- Auto-sets `DATABASE_URL` environment variable
- Sets up connection pooling

**Railway automatically provides:**
- `DATABASE_URL=postgresql://user:pass@host:port/db`
- Connection details in dashboard

---

### Step 3: Add Redis Cache
```bash
railway add --plugin redis
```

**What happens:**
- Creates Redis 7 instance
- Auto-sets `REDIS_URL` environment variable
- Configures for caching

---

### Step 4: Set Environment Variables
```bash
# Run the setup script
bash /tmp/railway-setup.sh

# Or set manually:
railway variables set YOUTUBE_API_KEY=your_youtube_api_key_here
railway variables set ENVIRONMENT=production
railway variables set SHARKS_TEAM_ID=SJS
railway variables set TIMEZONE=America/Los_Angeles
railway variables set REDIS_ENABLED=true
```

**Verify variables:**
```bash
railway variables
```

---

### Step 5: Deploy Backend
```bash
# Deploy from backend directory
cd backend
railway up

# Or deploy with specific service
railway up --service backend
```

**What happens:**
- Builds Docker image from `backend/Dockerfile`
- Pushes to Railway's container registry
- Deploys container with health checks
- Exposes public URL

**Expected output:**
```
✓ Building Docker image
✓ Pushing to registry
✓ Deploying...
✓ Deployment live at: https://your-app.railway.app
```

---

### Step 6: Run Database Migrations
```bash
# SSH into the running container
railway run alembic upgrade head

# Or run as one-off command
railway run bash -c "alembic upgrade head"
```

---

### Step 7: Deploy Frontend
```bash
# Create frontend service
railway service create frontend

# Deploy frontend
cd ../frontend
railway up --service frontend
```

---

### Step 8: Configure Frontend to Talk to Backend

Get your backend URL:
```bash
railway status --service backend
```

Set frontend environment variable:
```bash
railway variables set NEXT_PUBLIC_API_URL=https://your-backend.railway.app --service frontend
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────┐
│           Railway Project                   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌──────────────┐   │
│  │   Backend    │      │   Frontend   │   │
│  │  (FastAPI)   │◄────►│  (Next.js)   │   │
│  │  Port 8000   │      │  Port 3000   │   │
│  └──────┬───────┘      └──────────────┘   │
│         │                                   │
│         │                                   │
│  ┌──────▼───────┐      ┌──────────────┐   │
│  │  PostgreSQL  │      │    Redis     │   │
│  │  (Database)  │      │   (Cache)    │   │
│  └──────────────┘      └──────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Alternative: Deploy with Railway Config

Create `railway.toml` in project root:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
```

Then deploy:
```bash
railway up
```

---

## Verify Deployment

### 1. Check Services Status
```bash
railway status
```

### 2. View Logs
```bash
# Backend logs
railway logs --service backend

# Frontend logs
railway logs --service frontend

# Follow logs in real-time
railway logs --follow
```

### 3. Test Endpoints
```bash
# Health check
curl https://your-backend.railway.app/health

# API docs
open https://your-backend.railway.app/docs

# Frontend
open https://your-frontend.railway.app
```

---

## Environment Variables Reference

Railway automatically sets:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `PORT` - Port to bind to (Railway assigns dynamically)
- `RAILWAY_ENVIRONMENT` - Current environment (production/staging)

You need to set:
- `YOUTUBE_API_KEY` - YouTube Data API key
- `ENVIRONMENT` - App environment (production)
- `SHARKS_TEAM_ID` - Team abbreviation (SJS)
- `TIMEZONE` - Timezone for scheduling (America/Los_Angeles)
- `REDIS_ENABLED` - Enable Redis caching (true)
- `NEXT_PUBLIC_API_URL` - Backend URL for frontend

---

## Database Management

### Run Migrations
```bash
railway run alembic upgrade head
```

### Access Database Shell
```bash
railway connect postgres
```

### Backup Database
```bash
railway run pg_dump > backup.sql
```

### Restore Database
```bash
railway run psql < backup.sql
```

---

## Continuous Deployment

### Option 1: Railway GitHub Integration
1. Go to Railway dashboard
2. Click on service → Settings
3. Connect GitHub repository
4. Enable auto-deploys on push to `main`

### Option 2: GitHub Actions (Already Configured!)
Your CI/CD pipeline ([.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml)) automatically deploys when:
- Push to `main` branch
- All tests pass
- Docker images build successfully

Just set the GitHub secret:
```bash
# Get your Railway token
railway login --browserless

# Copy the token and add to GitHub secrets:
# Settings → Secrets → Actions → New repository secret
# Name: RAILWAY_TOKEN
# Value: <paste token>
```

---

## Monitoring

### View Metrics
```bash
railway metrics
```

### Check Deployments
```bash
railway deployments
```

### View Build Logs
```bash
railway logs --deployment <deployment-id>
```

---

## Troubleshooting

### Build Failing
```bash
# Check build logs
railway logs --deployment latest

# Test build locally
docker build -t test-backend ./backend
```

### Database Connection Error
```bash
# Verify DATABASE_URL is set
railway variables | grep DATABASE_URL

# Test connection
railway run python -c "import psycopg2; print('Connected!')"
```

### Health Check Failing
```bash
# Check health endpoint
railway logs --service backend | grep health

# SSH into container
railway run bash
curl localhost:8000/health
```

---

## Costs

Railway Free Plan:
- ✅ $5 of usage per month
- ✅ Unlimited projects
- ✅ PostgreSQL + Redis included
- ✅ Automatic SSL

Typical usage for this app: **~$3-4/month** (well within free tier)

---

## Next Steps After Deployment

1. ✅ Set up custom domain (optional)
2. ✅ Configure GitHub auto-deploys
3. ✅ Set up monitoring/alerts
4. ✅ Add Sentry for error tracking
5. ✅ Schedule data fetch cron job

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app
