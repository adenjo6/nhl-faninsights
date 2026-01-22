#!/bin/bash
# Pre-commit Security Check
# Run this before committing to ensure no secrets are exposed

set -e

echo "🔒 Running Pre-Commit Security Checks..."
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Check 1: Ensure .env is gitignored
echo "📝 Check 1: Verifying .env is gitignored..."
if git check-ignore .env > /dev/null 2>&1; then
    echo -e "${GREEN}✅ .env is properly gitignored${NC}"
else
    echo -e "${RED}❌ ERROR: .env is NOT gitignored!${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 2: Scan for API keys in staged files
echo "🔍 Check 2: Scanning staged files for API keys..."
if git diff --cached | grep -i "AIzaSy\|sk-ant-\|sk-proj-" > /dev/null 2>&1; then
    echo -e "${RED}❌ ERROR: Found potential API key in staged files!${NC}"
    echo "   Found matches:"
    git diff --cached | grep -i "AIzaSy\|sk-ant-\|sk-proj-" | head -5
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ No API keys found in staged files${NC}"
fi
echo ""

# Check 3: Scan for passwords in staged files
echo "🔍 Check 3: Scanning for hardcoded passwords..."
if git diff --cached | grep -E "(password|passwd|pwd).*=.*['\"][^'{]" | grep -v "secrets\." | grep -v "example" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  WARNING: Found potential hardcoded password${NC}"
    echo "   Please verify these are not real passwords:"
    git diff --cached | grep -E "(password|passwd|pwd).*=.*['\"][^'{]" | grep -v "secrets\." | grep -v "example" | head -3
else
    echo -e "${GREEN}✅ No hardcoded passwords found${NC}"
fi
echo ""

# Check 4: Verify .env.example exists
echo "📝 Check 4: Verifying .env.example exists..."
if [ -f ".env.example" ]; then
    echo -e "${GREEN}✅ .env.example exists${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING: .env.example not found${NC}"
fi
echo ""

# Check 5: Ensure .env.example has no real secrets
echo "🔍 Check 5: Checking .env.example for real secrets..."
if [ -f ".env.example" ]; then
    if grep -i "AIzaSy\|sk-ant-\|sk-proj-" .env.example > /dev/null 2>&1; then
        echo -e "${RED}❌ ERROR: .env.example contains real API keys!${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✅ .env.example has no real secrets${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipped (file not found)${NC}"
fi
echo ""

# Check 6: Check if .env is accidentally staged
echo "📝 Check 6: Verifying .env is not staged..."
if git diff --staged --name-only | grep "^.env$" > /dev/null 2>&1; then
    echo -e "${RED}❌ ERROR: .env file is staged for commit!${NC}"
    echo "   Run: git reset HEAD .env"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ .env is not staged${NC}"
fi
echo ""

# Check 7: Scan for database connection strings
echo "🔍 Check 7: Scanning for database URLs..."
if git diff --cached | grep -E "postgresql://.*:.*@" | grep -v "testuser:testpass" | grep -v "example" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  WARNING: Found database connection string${NC}"
    echo "   Verify this is not a production database URL"
else
    echo -e "${GREEN}✅ No production database URLs found${NC}"
fi
echo ""

# Summary
echo "========================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All security checks passed!${NC}"
    echo ""
    echo "Safe to commit. Run:"
    echo "  git commit -m 'your message'"
    exit 0
else
    echo -e "${RED}❌ $ERRORS security check(s) failed!${NC}"
    echo ""
    echo "Fix the issues above before committing."
    echo "To see what would be committed, run:"
    echo "  git diff --cached"
    exit 1
fi
