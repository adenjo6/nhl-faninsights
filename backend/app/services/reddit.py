"""
Reddit integration for game discussions.

Fetches top comments from r/SanJoseSharks game threads.
"""
import httpx
from typing import List, Dict, Optional
from datetime import datetime


async def search_game_thread(
    away_team: str,
    home_team: str,
    game_date: datetime,
    subreddit: str = "SanJoseSharks"
) -> Optional[str]:
    """
    Search for a game thread on Reddit.

    Returns the thread ID if found, None otherwise.
    """
    # Format search query
    date_str = game_date.strftime("%m/%d/%Y")
    query = f"{away_team} {home_team} {date_str}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.reddit.com/r/{subreddit}/search.json",
                params={
                    "q": query,
                    "restrict_sr": "on",
                    "sort": "relevance",
                    "limit": 5
                },
                headers={"User-Agent": "NHL-Fan-Insights/1.0"}
            )

            if response.status_code != 200:
                return None

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            # Find the game thread
            for post in posts:
                post_data = post.get("data", {})
                title = post_data.get("title", "").lower()

                # Look for game thread indicators
                if ("game thread" in title or "gdt" in title) and \
                   (away_team.lower() in title or home_team.lower() in title):
                    return post_data.get("id")

            return None

    except Exception as e:
        print(f"Error searching Reddit: {e}")
        return None


async def fetch_thread_comments(
    thread_id: str,
    subreddit: str = "SanJoseSharks",
    limit: int = 50,
    sort: str = "top"
) -> List[Dict]:
    """
    Fetch top comments from a Reddit thread.

    Args:
        thread_id: Reddit post ID
        subreddit: Subreddit name
        limit: Number of comments to fetch
        sort: Sort method (top, best, new, controversial)

    Returns:
        List of comment dictionaries with:
        - author: Username
        - body: Comment text
        - score: Upvotes
        - created_utc: Timestamp
        - permalink: Link to comment
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.reddit.com/r/{subreddit}/comments/{thread_id}.json",
                params={"sort": sort, "limit": limit},
                headers={"User-Agent": "NHL-Fan-Insights/1.0"}
            )

            if response.status_code != 200:
                return []

            data = response.json()

            # Reddit returns [post, comments]
            if len(data) < 2:
                return []

            comments_data = data[1].get("data", {}).get("children", [])

            parsed_comments = []
            for comment in comments_data:
                comment_data = comment.get("data", {})

                # Skip non-comment items (like "more" links)
                if comment_data.get("body") in [None, "[deleted]", "[removed]"]:
                    continue

                parsed_comments.append({
                    "author": comment_data.get("author", "Anonymous"),
                    "body": comment_data.get("body", ""),
                    "score": comment_data.get("score", 0),
                    "created_utc": datetime.fromtimestamp(
                        comment_data.get("created_utc", 0)
                    ).isoformat(),
                    "permalink": f"https://www.reddit.com{comment_data.get('permalink', '')}"
                })

            return parsed_comments

    except Exception as e:
        print(f"Error fetching Reddit comments: {e}")
        return []


async def get_game_reddit_discussion(
    away_team: str,
    home_team: str,
    game_date: datetime,
    limit: int = 50
) -> Dict:
    """
    Get Reddit discussion for a game.

    Returns:
        Dictionary with:
        - thread_id: Reddit thread ID (if found)
        - thread_url: Direct link to thread
        - comments: List of top comments
        - comment_count: Number of comments fetched
    """
    # Search for game thread
    thread_id = await search_game_thread(away_team, home_team, game_date)

    if not thread_id:
        return {
            "thread_id": None,
            "thread_url": None,
            "comments": [],
            "comment_count": 0
        }

    # Fetch comments
    comments = await fetch_thread_comments(thread_id, limit=limit)

    return {
        "thread_id": thread_id,
        "thread_url": f"https://www.reddit.com/r/SanJoseSharks/comments/{thread_id}",
        "comments": comments,
        "comment_count": len(comments)
    }
