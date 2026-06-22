"""
Reddit integration for game discussions.

Two public sync helpers drive the Phase 2+ pipeline:

- find_post_game_thread(...)  — listing scan of r/SanJoseSharks for the PGT
                                matching a specific Sharks game.
- fetch_thread_comments(...)  — pulls and prioritizes top-level comments from a
                                discovered thread per the Q5a selection strategy.

Each dispatches to one of two transports:

- PRAW (auth'd, ~100 req/min, robust)            — preferred, default
- Anonymous reddit.com/.json (~10 req/min)        — bridging fallback while
                                                    Reddit API access is pending.
                                                    Selected via REDDIT_USE_ANON=true.

The legacy async wrapper get_game_reddit_discussion(...) remains for backward
compatibility with the existing scheduler job and the /api/reddit endpoint;
it'll be deleted in Phase 5 when the live-comments endpoint is killed.
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.config import settings
from app.utils.teams import opponent_nickname

logger = logging.getLogger(__name__)


# Compiled once. Matches "Post-Game Thread", "Post Game Thread", "Postgame Thread",
# and "PGT:" / "PGT " at the start of a title. Case-insensitive.
PGT_TITLE_RE = re.compile(r"post.?game\s*thread|^pgt[\s:]", re.I)

# AutoMod typically posts the PGT 0-5 minutes after the buzzer. Average NHL game is
# ~2h 30-40m wall time; OT/SO can stretch to ~3h. Allow a window from puck-drop+2h
# (fastest blowout) to puck-drop+5h (OT+SO+AutoMod lag).
PGT_WINDOW_LOWER = timedelta(hours=2)
PGT_WINDOW_UPPER = timedelta(hours=5)

# Anonymous transport config
REDDIT_HTTP_BASE = "https://www.reddit.com"
REDDIT_HTTP_TIMEOUT = 15.0  # seconds
REDDIT_429_BACKOFF = 30      # seconds; one retry on rate-limit

# Reddit's anti-bot wall returns 403 + a 190KB HTML homepage to any UA matching
# "python:..." or any request lacking browser-shape headers — verified via
# diagnose_reddit.py against r/SanJoseSharks/new.json. Honest UAs only work
# against the OAuth-authenticated API (PRAW path). This header set is the
# minimum that passes the anon wall today; flipping back to PRAW with the
# settings.REDDIT_USER_AGENT happens automatically when REDDIT_USE_ANON=false.
_ANON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def _make_reddit_client():
    """Build a PRAW Reddit client, or return None if credentials are unset."""
    if not all([
        settings.REDDIT_CLIENT_ID,
        settings.REDDIT_CLIENT_SECRET,
        settings.REDDIT_USERNAME,
        settings.REDDIT_PASSWORD,
    ]):
        return None

    try:
        import praw
        return praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            username=settings.REDDIT_USERNAME,
            password=settings.REDDIT_PASSWORD,
            user_agent=settings.REDDIT_USER_AGENT,
            check_for_async=False,
        )
    except Exception as e:
        logger.error(f"Failed to initialize PRAW client: {e}")
        return None


# Module-level singleton. None when creds are missing (silent disable).
reddit = _make_reddit_client()


def _ensure_utc(dt: datetime) -> datetime:
    """Coerce a datetime to UTC. Naive datetimes are assumed UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Shared logic — title/window matching and comment selection.
# Both PRAW and anonymous paths normalize their inputs into the shapes these
# helpers expect, so prioritization is identical regardless of transport.
# ---------------------------------------------------------------------------


def _pgt_title_matches(title: str, opp_nick_lower: str) -> bool:
    """True if `title` looks like a PGT and contains the opponent's nickname."""
    if not PGT_TITLE_RE.search(title):
        return False
    if opp_nick_lower not in title.lower():
        return False
    return True


def _select_comments(candidates: list[dict]) -> list[dict]:
    """Q5a selection: top 30 by score + top 10 by reply count, dedupe, truncate.

    Each candidate must have keys: id, body, score, _reply_count, plus whatever
    other metadata (author, permalink, created_utc) the caller wants preserved.
    """
    by_score = sorted(candidates, key=lambda c: c["score"], reverse=True)[:30]
    by_replies = sorted(candidates, key=lambda c: c["_reply_count"], reverse=True)[:10]

    seen: set[str] = set()
    selected: list[dict] = []
    for c in by_score + by_replies:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        c.pop("_reply_count", None)
        c["body"] = c["body"][:800]
        selected.append(c)
    return selected


# ---------------------------------------------------------------------------
# PRAW transport
# ---------------------------------------------------------------------------


def _find_pgt_via_praw(
    away_team: str,
    home_team: str,
    game_date_utc: datetime,
    subreddit: Optional[str],
) -> Optional[tuple[str, datetime]]:
    sub_name = subreddit or settings.REDDIT_SUBREDDIT
    opp_nick = opponent_nickname(settings.SHARKS_TEAM_ID, away_team, home_team)
    if not opp_nick:
        logger.warning(
            f"No nickname mapping for opponent of {settings.SHARKS_TEAM_ID} in "
            f"{away_team}@{home_team}; cannot reliably match PGT title"
        )
        return None

    game_dt = _ensure_utc(game_date_utc)
    window_lower = game_dt + PGT_WINDOW_LOWER
    window_upper = game_dt + PGT_WINDOW_UPPER
    opp_nick_lower = opp_nick.lower()

    try:
        for submission in reddit.subreddit(sub_name).new(limit=100):
            title = submission.title or ""
            if not _pgt_title_matches(title, opp_nick_lower):
                continue
            created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
            if not (window_lower <= created <= window_upper):
                continue
            return submission.id, created.replace(tzinfo=None)
    except Exception as e:
        logger.error(f"PRAW listing scan failed for r/{sub_name}: {e}")
        return None

    return None


def _fetch_comments_via_praw(thread_id: str) -> list[dict]:
    try:
        submission = reddit.submission(id=thread_id)
        submission.comment_sort = "top"
        submission.comments.replace_more(limit=0)
        top_level = list(submission.comments)
    except Exception as e:
        logger.error(f"PRAW comment load failed for thread {thread_id}: {e}")
        return []

    candidates = []
    for c in top_level:
        body = getattr(c, "body", "") or ""
        if len(body) < 20:
            continue
        score = getattr(c, "score", 0) or 0
        if score < 1:
            continue
        author = getattr(c, "author", None)
        author_name = author.name if author else None
        if author_name == "AutoModerator":
            continue
        candidates.append({
            "id": c.id,
            "body": body,
            "score": score,
            "author": author_name,
            "permalink": f"https://www.reddit.com{c.permalink}" if getattr(c, "permalink", None) else None,
            "created_utc": getattr(c, "created_utc", None),
            "_reply_count": len(c.replies) if getattr(c, "replies", None) else 0,
        })

    return _select_comments(candidates)


# ---------------------------------------------------------------------------
# Anonymous transport
# ---------------------------------------------------------------------------


def _anon_get_json(path: str, params: Optional[dict] = None, _retried: bool = False):
    """Anonymous GET to reddit.com<path>. Returns parsed JSON, or None on failure."""
    url = f"{REDDIT_HTTP_BASE}{path}"
    try:
        with httpx.Client(timeout=REDDIT_HTTP_TIMEOUT) as client:
            resp = client.get(url, params=params, headers=_ANON_HEADERS, follow_redirects=True)
        if resp.status_code == 429 and not _retried:
            logger.warning(f"Reddit 429 on {url}; backing off {REDDIT_429_BACKOFF}s and retrying once")
            time.sleep(REDDIT_429_BACKOFF)
            return _anon_get_json(path, params=params, _retried=True)
        if resp.status_code != 200:
            logger.error(f"Reddit anon GET {url} -> HTTP {resp.status_code}")
            return None
        return resp.json()
    except Exception as e:
        logger.error(f"Reddit anon GET {url} failed: {e}")
        return None


def _find_pgt_via_anon(
    away_team: str,
    home_team: str,
    game_date_utc: datetime,
    subreddit: Optional[str],
) -> Optional[tuple[str, datetime]]:
    sub_name = subreddit or settings.REDDIT_SUBREDDIT
    opp_nick = opponent_nickname(settings.SHARKS_TEAM_ID, away_team, home_team)
    if not opp_nick:
        logger.warning(
            f"No nickname mapping for opponent of {settings.SHARKS_TEAM_ID} in "
            f"{away_team}@{home_team}; cannot reliably match PGT title"
        )
        return None

    data = _anon_get_json(f"/r/{sub_name}/new.json", params={"limit": 100})
    if not isinstance(data, dict):
        return None

    children = data.get("data", {}).get("children", [])
    game_dt = _ensure_utc(game_date_utc)
    window_lower = game_dt + PGT_WINDOW_LOWER
    window_upper = game_dt + PGT_WINDOW_UPPER
    opp_nick_lower = opp_nick.lower()

    for child in children:
        if child.get("kind") != "t3":  # t3 = submission
            continue
        post = child.get("data") or {}
        title = post.get("title") or ""
        if not _pgt_title_matches(title, opp_nick_lower):
            continue
        created_ts = post.get("created_utc")
        if created_ts is None:
            continue
        created = datetime.fromtimestamp(created_ts, tz=timezone.utc)
        if not (window_lower <= created <= window_upper):
            continue
        return post.get("id"), created.replace(tzinfo=None)

    return None


def _fetch_comments_via_anon(thread_id: str) -> list[dict]:
    sub_name = settings.REDDIT_SUBREDDIT
    data = _anon_get_json(
        f"/r/{sub_name}/comments/{thread_id}.json",
        params={"sort": "top", "limit": 100},
    )
    if not isinstance(data, list) or len(data) < 2:
        return []

    comments_listing = data[1].get("data", {}).get("children", []) if isinstance(data[1], dict) else []
    candidates = []

    for child in comments_listing:
        if child.get("kind") != "t1":  # skip "more" stubs
            continue
        c = child.get("data") or {}
        body = c.get("body") or ""
        if body in ("[deleted]", "[removed]"):
            continue
        if len(body) < 20:
            continue
        score = c.get("score", 0) or 0
        if score < 1:
            continue
        author = c.get("author")
        if author == "AutoModerator":
            continue
        replies = c.get("replies") or ""
        reply_count = 0
        if isinstance(replies, dict):
            reply_count = len(replies.get("data", {}).get("children", []))
        permalink = c.get("permalink")
        candidates.append({
            "id": c.get("id"),
            "body": body,
            "score": score,
            "author": author,
            "permalink": f"https://www.reddit.com{permalink}" if permalink else None,
            "created_utc": c.get("created_utc"),
            "_reply_count": reply_count,
        })

    return _select_comments(candidates)


# ---------------------------------------------------------------------------
# Public dispatchers
# ---------------------------------------------------------------------------


def find_post_game_thread(
    away_team: str,
    home_team: str,
    game_date_utc: datetime,
    subreddit: Optional[str] = None,
) -> Optional[tuple[str, datetime]]:
    """Find the Reddit Post-Game Thread for a Sharks game.

    Strategy: scan the most recent 100 posts in the configured subreddit, keep
    posts whose title matches the PGT regex AND contain the opponent's nickname
    AND were created within [game_start + 2h, game_start + 5h].

    Returns:
        (thread_id, thread_created_at_utc) on a match, else None. The
        thread_created_at is a naive UTC datetime to match the rest of the model.
    """
    if settings.REDDIT_USE_ANON:
        return _find_pgt_via_anon(away_team, home_team, game_date_utc, subreddit)
    if reddit is None:
        logger.debug("PRAW client not configured and REDDIT_USE_ANON=false; skipping discovery")
        return None
    return _find_pgt_via_praw(away_team, home_team, game_date_utc, subreddit)


def fetch_thread_comments(thread_id: str) -> list[dict]:
    """Fetch and prioritize top-level comments from a thread for sentiment analysis.

    Q5a selection strategy: top-level only; drop AutoMod and score < 1; drop
    bodies under 20 chars; take top 30 by score plus top 10 by reply count;
    de-dupe by id; truncate body to 800 chars.

    Returns a list of dicts: {id, body, score, author, permalink, created_utc}.
    Empty list on any failure (caller decides whether to retry).
    """
    if settings.REDDIT_USE_ANON:
        return _fetch_comments_via_anon(thread_id)
    if reddit is None:
        logger.debug("PRAW client not configured and REDDIT_USE_ANON=false; skipping comment fetch")
        return []
    return _fetch_comments_via_praw(thread_id)


# ---------------------------------------------------------------------------
# Legacy async wrapper. Kept for backward compatibility with the current
# scheduler job and /api/reddit endpoint. Will be deleted in Phase 5.
# ---------------------------------------------------------------------------


def _get_game_reddit_discussion_sync(
    away_team: str,
    home_team: str,
    game_date: datetime,
    limit: int,
    subreddit: Optional[str],
) -> dict:
    sub_name = subreddit or settings.REDDIT_SUBREDDIT
    found = find_post_game_thread(away_team, home_team, game_date, subreddit=sub_name)
    if not found:
        return {
            "thread_id": None,
            "thread_url": None,
            "comments": [],
            "comment_count": 0,
        }

    thread_id, _created_at = found
    comments = fetch_thread_comments(thread_id)
    if limit and len(comments) > limit:
        comments = comments[:limit]

    return {
        "thread_id": thread_id,
        "thread_url": f"https://www.reddit.com/r/{sub_name}/comments/{thread_id}",
        "comments": comments,
        "comment_count": len(comments),
    }


async def get_game_reddit_discussion(
    away_team: str,
    home_team: str,
    game_date: datetime,
    limit: int = 50,
    subreddit: Optional[str] = None,
) -> dict:
    """Legacy async façade — runs the new sync helpers in a thread.

    Returns the same shape as the pre-Phase-2 implementation:
        { thread_id, thread_url, comments, comment_count }
    """
    return await asyncio.to_thread(
        _get_game_reddit_discussion_sync,
        away_team,
        home_team,
        game_date,
        limit,
        subreddit,
    )
