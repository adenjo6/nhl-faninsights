#!/bin/bash
# Quick Deploy Script for Railway
# Deploys NHL Fan Insights to Railway in one command

set -e  # Exit on error

echo "🚀 NHL Fan Insights - Railway Deployment"
echo "=========================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please login:"
    railway login
fi

echo "✅ Railway CLI ready"
echo ""

# Step 1: Initialize project
echo "📦 Step 1: Initializing Railway project..."
if [ ! -f ".railway/project.json" ]; then
    railway init
else
    echo "   Project already initialized"
fi
echo ""

# Step 2: Add PostgreSQL
echo "🗄️  Step 2: Adding PostgreSQL database..."
railway add --plugin postgresql || echo "   PostgreSQL may already exist"
echo ""

# Step 3: Add Redis
echo "⚡ Step 3: Adding Redis cache..."
railway add --plugin redis || echo "   Redis may already exist"
echo ""

# Step 4: Set environment variables
echo "🔧 Step 4: Setting environment variables..."

# Load API key from .env file
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    railway variables set YOUTUBE_API_KEY=$YOUTUBE_API_KEY
else
    echo "⚠️  Warning: .env file not found. Please set YOUTUBE_API_KEY manually:"
    echo "   railway variables set YOUTUBE_API_KEY=your_key_here"
fi

railway variables set ENVIRONMENT=production
railway variables set SHARKS_TEAM_ID=SJS
railway variables set TIMEZONE=America/Los_Angeles
railway variables set REDIS_ENABLED=true
echo ""

# Step 5: Deploy backend
echo "🚀 Step 5: Deploying backend..."
cd backend
railway up || echo "   Backend deployment initiated"
cd ..
echo ""

# Step 6: Run migrations
echo "🔄 Step 6: Running database migrations..."
railway run alembic upgrade head
echo ""

# Step 7: Get backend URL
echo "🌐 Step 7: Getting backend URL..."
BACKEND_URL=$(railway status --json | grep -o '"url":"[^"]*"' | cut -d'"' -f4 || echo "")
if [ -n "$BACKEND_URL" ]; then
    echo "   Backend URL: $BACKEND_URL"
else
    echo "   ⚠️  Could not auto-detect backend URL. Check Railway dashboard."
fi
echo ""

# Step 8: Deploy frontend (optional)
read -p "Deploy frontend? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🎨 Step 8: Deploying frontend..."

    # Create frontend service if needed
    railway service create frontend 2>/dev/null || echo "   Frontend service may already exist"

    # Set frontend environment variable
    if [ -n "$BACKEND_URL" ]; then
        railway variables set NEXT_PUBLIC_API_URL=$BACKEND_URL --service frontend
    fi

    cd frontend
    railway up --service frontend
    cd ..
fi
echo ""

echo "✅ Deployment Complete!"
echo "======================="
echo ""
echo "Next steps:"
echo "1. Check deployment status: railway status"
echo "2. View logs: railway logs --follow"
echo "3. Open dashboard: railway open"
echo ""
echo "Test your API:"
if [ -n "$BACKEND_URL" ]; then
    echo "  curl $BACKEND_URL/health"
    echo "  open $BACKEND_URL/docs"
else
    echo "  Run 'railway status' to get your URL"
fi
echo ""
echo "📚 Full guide: see DEPLOYMENT.md"
