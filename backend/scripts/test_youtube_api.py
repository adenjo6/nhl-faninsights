#!/usr/bin/env python3
"""
Test YouTube API connectivity and search functionality.
"""
from app.config import settings
from datetime import datetime

print("="*70)
print("YouTube API Test")
print("="*70)

# Step 1: Check if API key is configured
print("\n1. Checking API key configuration...")
if settings.YOUTUBE_API_KEY:
    print(f"   ✓ API key found: {settings.YOUTUBE_API_KEY[:20]}...")
else:
    print("   ❌ No API key found in settings!")
    exit(1)

# Step 2: Try to import and build YouTube client
print("\n2. Testing YouTube client initialization...")
try:
    from googleapiclient.discovery import build
    youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
    print("   ✓ YouTube client built successfully")
except ImportError as e:
    print(f"   ❌ Missing google-api-python-client: {e}")
    print("   Run: pip install google-api-python-client")
    exit(1)
except Exception as e:
    print(f"   ❌ Error building YouTube client: {e}")
    exit(1)

# Step 3: Test a simple search
print("\n3. Testing YouTube API search...")
try:
    # Search for recent Sharks highlights
    test_search = youtube.search().list(
        q="San Jose Sharks highlights",
        type="video",
        part="id,snippet",
        maxResults=1
    ).execute()

    if test_search.get("items"):
        item = test_search["items"][0]
        print(f"   ✓ Search successful!")
        print(f"   Found video: {item['snippet']['title']}")
        print(f"   Video ID: {item['id']['videoId']}")
    else:
        print("   ⚠️  Search returned no results")
except Exception as e:
    print(f"   ❌ Search failed: {e}")
    if "quotaExceeded" in str(e):
        print("   → You've exceeded your daily YouTube API quota (10,000 units)")
    elif "API key not valid" in str(e):
        print("   → Your API key is invalid. Check it in .env file")
    exit(1)

# Step 4: Test search for a specific game
print("\n4. Testing game-specific search...")
try:
    # Test with a recent completed game: VAN @ SJS on Nov 28, 2025
    query = "VAN vs SJS highlights November 28 2025"
    game_date = datetime(2025, 11, 28)

    nhl_search = youtube.search().list(
        q=query,
        channelId="UCqFMzb-4AUf6WAIbl132QKA",  # Official NHL channel
        type="video",
        part="id,snippet",
        maxResults=1,
        order="date",
        publishedAfter=game_date.isoformat() + "Z"
    ).execute()

    if nhl_search.get("items"):
        item = nhl_search["items"][0]
        snippet = item["snippet"]
        print(f"   ✓ NHL Official search successful!")
        print(f"   Video: {snippet['title']}")
        print(f"   Channel: {snippet['channelTitle']}")
        print(f"   Video ID: {item['id']['videoId']}")
        print(f"   Published: {snippet['publishedAt']}")
    else:
        print("   ⚠️  No NHL official highlights found for this game")
        print(f"   Query: {query}")
        print(f"   Published after: {game_date.isoformat()}")
except Exception as e:
    print(f"   ❌ NHL channel search failed: {e}")

# Step 5: Test the actual service function
print("\n5. Testing search_game_highlights() function...")
try:
    from app.services.youtube import search_game_highlights

    # Test with VAN @ SJS game
    videos = search_game_highlights(
        away_team="VAN",
        home_team="SJS",
        game_date=datetime(2025, 11, 28),
        max_results=2
    )

    print(f"   ✓ Function executed")
    print(f"   NHL Official: {videos.get('nhl_official')}")
    print(f"   Professor Hockey: {videos.get('professor_hockey')}")

    if videos.get('nhl_official'):
        print(f"\n   ✅ NHL video data structure:")
        for key, value in videos['nhl_official'].items():
            print(f"      {key}: {value}")
    else:
        print(f"\n   ⚠️  No NHL official video found")

except Exception as e:
    print(f"   ❌ Function failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("Test complete!")
print("="*70)
