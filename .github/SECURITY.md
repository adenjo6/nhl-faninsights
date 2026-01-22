# Security Policy

## Reporting Security Issues

If you discover a security vulnerability, please email adenjo@ucsb.edu instead of using the issue tracker.

## Secure Configuration

### Environment Variables

**NEVER commit these files:**
- `.env` - Contains API keys and secrets
- `.env.local`, `.env.production`, `.env.development`
- Any file with actual credentials

**Always commit:**
- `.env.example` - Template without real values
- Configuration with `secrets.*` references for CI/CD

### API Keys and Secrets

This project uses the following secrets:

1. **YOUTUBE_API_KEY** - YouTube Data API v3 key
   - Required for fetching game videos
   - Get yours at: https://console.cloud.google.com/apis/credentials
   - Set in `.env` for local development
   - Set in Railway/Render for production
   - Set as GitHub Secret for CI/CD

2. **CLAUDE_API_KEY** (Optional) - Anthropic API key
   - Used for AI-generated game recaps
   - Get yours at: https://console.anthropic.com/
   - Optional for basic functionality

3. **DATABASE_URL** - PostgreSQL connection string
   - Automatically set by Railway/Render
   - Format: `postgresql://user:password@host:port/database`
   - Never commit actual database URLs

4. **REDIS_URL** - Redis connection string
   - Automatically set by Railway/Render
   - Never commit actual Redis URLs

### GitHub Actions Secrets

Configure these in repository settings (Settings → Secrets → Actions):

- `YOUTUBE_API_KEY` - For running tests
- `RAILWAY_TOKEN` - For automated deployments (optional)
- `RENDER_DEPLOY_HOOK` - For Render deployments (optional)
- `GITHUB_TOKEN` - Automatically provided by GitHub

### Docker Security

- Multi-stage builds minimize attack surface
- Non-root users in containers (`appuser`, `nextjs`)
- No secrets in Docker images
- Health checks for reliability
- Read-only file systems where possible

### Database Security

- Connection pooling enabled
- Prepared statements (SQLAlchemy ORM)
- Input validation with Pydantic
- No raw SQL queries
- Regular backups on production

### Best Practices

1. **Never commit secrets** - Use `.env.example` as template
2. **Rotate API keys** - If accidentally exposed, regenerate immediately
3. **Use environment variables** - Never hardcode credentials
4. **Review before commit** - Check `git diff` for secrets
5. **Enable branch protection** - Require PR reviews for main branch
6. **Keep dependencies updated** - Run `npm audit` and `pip check` regularly

### Pre-Commit Checklist

Before pushing to GitHub:

```bash
# 1. Check for secrets
git diff | grep -i "api_key\|password\|secret\|token"

# 2. Verify .env is gitignored
git check-ignore .env

# 3. Review staged changes
git diff --staged

# 4. Ensure .env.example has no real values
cat .env.example
```

### If You Accidentally Commit a Secret

1. **Revoke the secret immediately** (regenerate API keys)
2. **Remove from Git history**:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/file" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push** (if safe to do so):
   ```bash
   git push origin --force --all
   ```
4. **Notify team members** to pull latest changes

## Vulnerability Disclosure

We take security seriously. If you find a vulnerability:

1. **DO NOT** open a public issue
2. Email adenjo@ucsb.edu with details
3. Include steps to reproduce
4. Allow reasonable time for fix before public disclosure

## Security Updates

- Dependencies are monitored via Dependabot
- Security patches applied within 48 hours
- Critical vulnerabilities addressed immediately
