# 🏒 NHL Fan Insights

**San Jose Sharks Game Recaps with Video Highlights, AI Summaries & Fan Discussion - Full Stack App with CI/CD**

[![CI Pipeline](https://github.com/adenjo6/nhl-faninsights/actions/workflows/ci.yml/badge.svg)](https://github.com/adenjo6/nhl-faninsights/actions)
[![Deploy Backend](https://github.com/adenjo6/nhl-faninsights/actions/workflows/cd-backend.yml/badge.svg)](https://github.com/adenjo6/nhl-faninsights/actions)

---

## 🎯 What This Is

An automated platform that fetches and displays San Jose Sharks game recaps with:
- **NHL Official Highlights** (from NHL's YouTube)
- **Professor Hockey Analysis** (detailed game breakdowns)
- **AI-Generated Game Recaps** (powered by Claude AI)
- **Fan Comments & Discussion** (authenticated user comments with threading)
- **Reddit Integration** (game threads from r/SanJoseSharks)
- **Player Tracking** (milestones, stats, team history)
- **Automatic game tracking** (scheduler checks for new games hourly)
- **Zero manual work** (everything automated)

---

## ✨ Features

- 🎥 **Embedded YouTube Videos**: 2 videos per game (NHL + Professor Hockey)
- 🤖 **Automated Fetching**: Scheduler runs hourly with staggered processing stages
- 🧠 **AI-Powered Recaps**: Claude API generates game summaries from play-by-play data
- 💬 **Fan Comments**: Authenticated users can discuss games with threaded replies
- 🔐 **User Authentication**: Clerk integration with role-based access control
- 🔴 **Reddit Integration**: Links to r/SanJoseSharks game threads
- 📊 **Player Tracking**: Career milestones, team history, and per-game stats
- 💾 **Redis Caching**: 5-minute cache for improved performance
- 📈 **Standings Snapshots**: Historical standings data captured per game
- 🏆 **Prospects Directory**: Sharks prospects with Elite Prospects links
- 🚀 **Full CI/CD**: Automated testing and deployment
- 🐳 **Docker**: Containerized for easy local development
- 📱 **Responsive UI**: Works on desktop and mobile

---

## 🛠️ Tech Stack

### Frontend
- **Next.js 15** (React framework)
- **TypeScript** (type safety)
- **Tailwind CSS** (styling)
- **Deployed on Vercel** (free CDN)

### Backend
- **FastAPI 0.116.1** (Python web framework)
- **PostgreSQL** (database with Alembic migrations)
- **SQLAlchemy 2.0** (ORM)
- **APScheduler 3.10** (background jobs with staggered processing)
- **Redis** (caching layer)
- **Pydantic** (data validation)
- **Deployed on Railway** ($8-15/month)

### Authentication & Security
- **Clerk** (user authentication and management)
- **JWT tokens** (API authentication)
- **Role-based access control** (user/admin permissions)

### CI/CD
- **GitHub Actions** (automation)
- **Docker** (containerization)
- **pytest** (Python testing with async support)
- **ESLint** (TypeScript linting)

### External APIs
- **NHL Stats API** (game data, boxscores, play-by-play - free)
- **YouTube Data API v3** (video search - free tier)
- **Anthropic Claude API** (AI-generated recaps)
- **Reddit API** (game thread discussions)
- **Clerk API** (user authentication)

---

## 🚀 Quick Start

### Option 1: Docker (Recommended for Development)

```bash
# 1. Clone repo
git clone https://github.com/adenjo6/nhl-faninsights.git
cd nhl-faninsights

# 2. Add YouTube API key
cp backend/.env.example backend/.env
# Edit backend/.env with your YouTube API key

# 3. Start everything
docker-compose up -d

# 4. Run migrations
docker-compose exec backend alembic upgrade head

# 5. Open app
open http://localhost:3000
```

**Full Docker guide**: [DOCKER_GUIDE.md](DOCKER_GUIDE.md)

### Option 2: Deploy to Production

**Full deployment guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

**Quick steps:**
1. Get YouTube API key ([instructions](DEPLOYMENT_GUIDE.md#prerequisites))
2. Deploy backend to Railway
3. Deploy frontend to Vercel
4. Set up GitHub Actions secrets

**Time to deploy**: ~20 minutes

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Complete Railway + Vercel deployment |
| [DOCKER_GUIDE.md](DOCKER_GUIDE.md) | Local development with Docker |
| [CI_CD_COMPLETE.md](CI_CD_COMPLETE.md) | CI/CD pipeline details |
| [WEEK1_COMPLETE.md](WEEK1_COMPLETE.md) | Initial development summary |

---

## 🏗️ Architecture

```
┌─────────────────┐
│   User Browser  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  Next.js        │──────▶│  FastAPI Backend │──────▶│   Redis Cache    │
│  (Vercel)       │       │  (Railway)       │       │   (5min TTL)     │
│  - Game list    │       │  - REST API      │       └──────────────────┘
│  - Video pages  │       │  - Scheduler     │
│  - Comments     │       │  - Auth (Clerk)  │       ┌──────────────────┐
│  - Reddit       │       │  - Background    │──────▶│  PostgreSQL      │
└─────────────────┘       │    jobs          │       │  (Railway)       │
                          └────────┬─────────┘       │  - Games         │
                                   │                 │  - Videos        │
                                   │                 │  - Users         │
                                   ▼                 │  - Comments      │
                          ┌────────────────┐         │  - Players       │
                          │  APScheduler   │         │  - Milestones    │
                          │  - Hourly jobs │         │  - Quotes        │
                          │  - Staggered   │         └──────────────────┘
                          │    processing  │
                          └────────────────┘

External APIs:
├─ NHL Stats API (game data, boxscores, play-by-play)
├─ YouTube Data API (video search)
├─ Claude API (AI-generated recaps)
├─ Reddit API (game threads)
└─ Clerk API (user authentication)
```

---

## 🔄 How It Works

### Game Processing Flow (Staggered Pipeline)

```
1. Scheduler runs hourly
   ↓
2. Check upcoming Sharks games → Create in DB as SCHEDULED
   ↓
3. Game starts → Status: LIVE
   ↓
4. Game ends → Status: FINAL
   ↓
5. T+0min: Immediate Processing
   - Fetch basic game data (score, status)
   - basic_stats_fetched = True
   ↓
6. T+2hr: Detailed Stats
   - Fetch boxscore (player stats)
   - Fetch play-by-play data
   ↓
7. T+4hr: Reddit Discussion
   - Find r/SanJoseSharks game thread
   - Store Reddit link
   - reddit_fetched = True
   ↓
8. T+12hr: Videos & AI Recap
   - Search YouTube for NHL highlights
   - Search for Professor Hockey recap
   - Generate AI recap with Claude
   - videos_fetched = True
   ↓
9. T+24hr: Quotes & Archive
   - Fetch post-game quotes
   - quotes_fetched = True
   - Status: ARCHIVED
   ↓
10. Display on frontend with Redis caching
```

### CI/CD Flow

```
1. Developer pushes code
   ↓
2. GitHub Actions CI
   - Run tests
   - Lint code
   - Build Docker images
   ↓
3. Tests pass? ✅
   ↓
4. GitHub Actions CD
   - Build production image
   - Push to registry
   - Deploy to Railway
   ↓
5. Live in ~5 minutes 🎉
```

---

## 🧪 Testing

### Run Tests Locally

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend lint
cd frontend
npm run lint

# Frontend TypeScript check
npm run type-check
```

### With Docker

```bash
docker-compose exec backend pytest tests/ -v
docker-compose exec frontend npm run lint
```

---

## 💰 Cost

### Monthly Costs
```
Railway Backend:       $8-15/month
Railway PostgreSQL:    Included
Vercel Frontend:       $0 (free tier)
GitHub Actions:        $0 (free tier)
YouTube API:           $0 (free tier)
─────────────────────────────────
Total:                 $8-15/month
```

### Free Tier Limits
- **Railway**: $5 free credit/month (often covers small apps)
- **Vercel**: 100GB bandwidth, unlimited sites
- **GitHub Actions**: 2000 minutes/month
- **YouTube API**: 10,000 quota units/day (~3,000 searches)

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

```bash
# Required
DATABASE_URL=postgresql://user:password@host:port/dbname
YOUTUBE_API_KEY=your_youtube_api_key_here
CLERK_SECRET_KEY=your_clerk_secret_key_here

# Optional - External Services
CLAUDE_API_KEY=your_claude_api_key_here  # For AI recaps
REDDIT_CLIENT_ID=your_reddit_client_id   # For Reddit integration
REDDIT_CLIENT_SECRET=your_reddit_secret

# Optional - Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional - Configuration
SHARKS_TEAM_ID=SJS
TIMEZONE=America/Los_Angeles
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
# Production: https://your-backend.railway.app

# Optional - Clerk (for authentication UI)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

---

## 📁 Project Structure

```
nhl-faninsights/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app with lifespan context
│   │   ├── config.py                # Pydantic settings
│   │   ├── scheduler.py             # APScheduler configuration
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── game.py             # Game model (scores, status, recap)
│   │   │   ├── video.py            # Video model (YouTube embeds)
│   │   │   ├── user.py             # User model (Clerk integration)
│   │   │   ├── comment.py          # Comment model (threaded replies)
│   │   │   ├── player.py           # Player stats (per-game)
│   │   │   ├── player_team_history.py  # Career tracking
│   │   │   ├── quote.py            # Post-game quotes
│   │   │   └── milestone.py        # Player milestones
│   │   │
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── game.py
│   │   │   ├── comment.py
│   │   │   └── recap.py
│   │   │
│   │   ├── crud/                    # Database operations
│   │   │   ├── game.py
│   │   │   ├── video.py
│   │   │   ├── comment.py
│   │   │   └── recap.py
│   │   │
│   │   ├── api/v1/                  # REST API endpoints
│   │   │   ├── deps.py             # Dependency injection
│   │   │   └── routers/
│   │   │       ├── games.py        # Game CRUD + list
│   │   │       ├── recap.py        # Recap endpoints
│   │   │       ├── comments.py     # Comment CRUD
│   │   │       ├── reddit.py       # Reddit integration
│   │   │       ├── prospects.py    # Prospects directory
│   │   │       └── monitoring.py   # Health checks
│   │   │
│   │   ├── services/                # External API integrations
│   │   │   ├── nhl.py              # NHL Stats API
│   │   │   ├── youtube.py          # YouTube Data API
│   │   │   ├── claude.py           # Claude AI recaps
│   │   │   ├── reddit.py           # Reddit API
│   │   │   └── redis_cache.py      # Redis caching
│   │   │
│   │   ├── jobs/                    # Background processing
│   │   │   ├── game_processor.py   # Staggered game processing
│   │   │   ├── roster_sync.py      # Roster updates
│   │   │   └── standings.py        # Standings snapshots
│   │   │
│   │   ├── auth/
│   │   │   └── clerk.py            # Clerk authentication
│   │   │
│   │   └── db/
│   │       └── session.py          # SQLAlchemy session
│   │
│   ├── alembic/                     # Database migrations
│   ├── tests/                       # pytest tests
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── pages/
│   │   ├── index.tsx               # Homepage with game list
│   │   ├── _app.tsx                # Next.js app wrapper
│   │   ├── _document.tsx           # HTML document
│   │   ├── game/[gameId].tsx       # Game detail with videos
│   │   ├── recap/[gameId].tsx      # Recap with Reddit
│   │   └── api/                    # Next.js API routes
│   │       ├── health.ts
│   │       └── reddit/
│   │
│   ├── lib/
│   │   └── reddit.ts               # Reddit utilities
│   │
│   ├── styles/
│   │   └── globals.css             # Tailwind CSS
│   │
│   ├── public/
│   ├── tsconfig.json               # TypeScript config
│   ├── tailwind.config.js
│   ├── next.config.ts
│   └── package.json
│
├── .github/workflows/
│   ├── ci.yml                      # CI pipeline
│   └── cd-backend.yml              # CD pipeline
│
├── docker-compose.yml              # Local dev stack
└── README.md                       # This file
```

---

## 🤝 Contributing

This is a personal project, but feel free to:
- Open issues for bugs
- Suggest features
- Fork and customize for your own team

---

## 📄 License

MIT License - Feel free to use this for your own NHL team!

---

## 🙏 Credits

- **NHL Stats API**: Game data, boxscores, and play-by-play
- **YouTube Data API**: Video search and metadata
- **Anthropic Claude**: AI-powered game recaps
- **Professor Hockey**: In-depth game analysis videos
- **Reddit API**: Community game thread discussions
- **Clerk**: User authentication and management
- **Railway**: Backend hosting and PostgreSQL
- **Vercel**: Frontend hosting and CDN
- **Redis**: Caching layer

---

## 🐛 Troubleshooting

### Common Issues

**Problem**: Backend won't start
```bash
# Check logs
docker-compose logs backend

# Common fix: missing API key
echo "YOUTUBE_API_KEY=your_key" >> backend/.env
```

**Problem**: Frontend can't connect to backend
```bash
# Check NEXT_PUBLIC_API_URL
cat frontend/.env.local

# Should be: http://localhost:8000 (local)
# or: https://your-backend.railway.app (prod)
```

**Problem**: No games showing
```bash
# Check if games exist in database
docker-compose exec backend python -c "from app.db.session import SessionLocal; from app.models import Game; db = SessionLocal(); print(db.query(Game).count())"

# If 0, scheduler needs to run or manually trigger
```

More help: [Troubleshooting Guide](DEPLOYMENT_GUIDE.md#troubleshooting)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/adenjo6/nhl-faninsights/issues)
- **Docs**: See documentation files above
- **Railway**: [docs.railway.app](https://docs.railway.app)
- **Vercel**: [vercel.com/docs](https://vercel.com/docs)

---

## 🚀 Roadmap

### ✅ Completed (Current State)
- [x] Automated game tracking with hourly scheduler
- [x] YouTube video fetching (NHL + Professor Hockey)
- [x] Full CI/CD pipeline with GitHub Actions
- [x] Docker setup for local development
- [x] User authentication with Clerk
- [x] Comments system with threaded replies
- [x] Player stats tracking (per-game)
- [x] AI-generated recaps (Claude)
- [x] Reddit integration (game threads)
- [x] Redis caching layer
- [x] Player milestones tracking
- [x] Post-game quotes
- [x] Standings snapshots
- [x] Prospects directory
- [x] Health monitoring endpoints
- [x] Staggered processing pipeline (T+0, T+2h, T+4h, T+12h, T+24h)

### 🚧 In Progress / Next Up
- [ ] Enhanced player stats pages (career view, advanced metrics)
- [ ] Comment reactions (upvotes/downvotes)
- [ ] User profiles and comment history
- [ ] Email notifications for new games
- [ ] Admin dashboard for managing content

### 🔮 Future Enhancements
- [ ] Real-time game updates (live scores during games)
- [ ] Push notifications (PWA)
- [ ] Advanced analytics dashboard
- [ ] Multi-team support (expand beyond Sharks)
- [ ] Mobile app (React Native)
- [ ] Fantasy hockey integration
- [ ] Betting odds integration
- [ ] Social sharing features

---

## ⭐ Star This Repo

If you find this useful, give it a star! ⭐

---

**Built with ❤️ for San Jose Sharks fans 🦈**

**Go Sharks! 🏒**
