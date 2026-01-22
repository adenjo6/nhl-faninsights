# GitHub Actions CI/CD Workflows

This directory contains automated workflows for continuous integration and deployment.

## Workflows

### 1. `ci-cd.yml` - Main CI/CD Pipeline
**Triggers:** Push to `main` or `develop`, Pull requests

**Jobs:**
- **Backend CI**: Runs tests, linting, and type checking for Python backend
  - Sets up PostgreSQL and Redis services
  - Installs dependencies and runs pytest with coverage
  - Uploads coverage reports to Codecov

- **Frontend CI**: Runs tests, linting, and builds Next.js app
  - Installs Node.js dependencies
  - Runs ESLint and TypeScript type checking
  - Builds production bundle

- **Docker Build**: Builds and pushes Docker images (main branch only)
  - Builds backend and frontend Docker images
  - Pushes to GitHub Container Registry (ghcr.io)
  - Uses layer caching for faster builds

- **Deploy**: Deploys to production (main branch only)
  - Supports Railway and Render deployments
  - Requires deployment secrets to be configured

### 2. `test.yml` - Test Suite
**Triggers:** Pull requests, manual dispatch

**Jobs:**
- **Backend Tests**: Complete test suite with database migrations
- **Frontend Tests**: Linting, type checking, and build verification

### 3. `docker-test.yml` - Docker Integration Test
**Triggers:** PR changes to Dockerfiles or docker-compose.yml

**Jobs:**
- **Docker Compose Test**: Full stack integration test
  - Builds all Docker images
  - Starts complete stack (backend, frontend, PostgreSQL, Redis)
  - Runs health checks and API tests
  - Verifies database migrations

## Required Secrets

Configure these in your GitHub repository settings (Settings → Secrets → Actions):

### Required for Tests
- `YOUTUBE_API_KEY` - YouTube Data API key for video fetching

### Optional for Deployment
- `RAILWAY_TOKEN` - Railway CLI token for deployment
- `RENDER_DEPLOY_HOOK` - Render deploy hook URL
- `CLAUDE_API_KEY` - Anthropic API key (optional)

### Automatic Secrets
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

## Branch Strategy

- **`main`**: Production branch
  - Full CI/CD pipeline runs
  - Docker images built and pushed
  - Auto-deploys to production

- **`develop`**: Development branch
  - CI tests run
  - No deployment

- **Feature branches**: Create PRs to `develop` or `main`
  - Test workflows run
  - Docker integration tests run (if Dockerfiles changed)

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run all workflows
act

# Run specific workflow
act -W .github/workflows/test.yml

# Run specific job
act -j backend-tests
```

## Monitoring

- **Test Results**: View in PR checks and Actions tab
- **Coverage Reports**: Uploaded to Codecov (if configured)
- **Docker Images**: Available at `ghcr.io/[username]/nhlfaninsights/backend` and `frontend`
- **Deployment Status**: Check Actions tab for deployment logs

## Performance

- **Backend CI**: ~2-3 minutes
- **Frontend CI**: ~2-3 minutes
- **Docker Build**: ~5-7 minutes (first build), ~2-3 minutes (cached)
- **Deploy**: ~1-2 minutes

Total pipeline time: **~5-10 minutes** for full CI/CD on main branch

## Troubleshooting

### Tests Failing
1. Check if all required secrets are configured
2. Review test logs in Actions tab
3. Ensure local tests pass first

### Docker Build Failing
1. Test locally with `docker compose up --build`
2. Check Dockerfile syntax
3. Verify all required files are not in `.dockerignore`

### Deployment Failing
1. Verify deployment secrets are correct
2. Check deployment platform (Railway/Render) logs
3. Ensure Docker images were built successfully

## Future Enhancements

- [ ] Add end-to-end tests with Playwright
- [ ] Set up automated security scanning
- [ ] Add performance benchmarking
- [ ] Implement blue-green deployments
- [ ] Add Slack/Discord notifications
