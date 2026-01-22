#!/usr/bin/env python3
"""Check what game types are in the database."""
from app.db.session import SessionLocal
from app.models.game import Game

db = SessionLocal()

# Get all games
games = db.query(Game).order_by(Game.game_date_utc).all()

print(f'Total games in database: {len(games)}\n')

# Check game types
preseason = []
regular_season = []
unknown = []

for game in games:
    if game.raw and 'gameType' in game.raw:
        game_type = game.raw['gameType']
        if game_type == 1:
            preseason.append(game)
        elif game_type == 2:
            regular_season.append(game)
        else:
            unknown.append(game)
    else:
        unknown.append(game)

print(f'Preseason games (gameType=1): {len(preseason)}')
print(f'Regular season games (gameType=2): {len(regular_season)}')
print(f'Unknown game type: {len(unknown)}')

if preseason:
    print('\n=== PRESEASON GAMES (should be ZERO!) ===')
    for game in preseason[:5]:
        print(f'  {game.game_id}: {game.away_team} @ {game.home_team} on {game.game_date_utc.date()} - Status: {game.status}')

if regular_season:
    print('\n=== REGULAR SEASON GAMES ===')
    print(f'First regular season game: {regular_season[0].away_team} @ {regular_season[0].home_team} on {regular_season[0].game_date_utc.date()}')
    print(f'Last regular season game: {regular_season[-1].away_team} @ {regular_season[-1].home_team} on {regular_season[-1].game_date_utc.date()}')

    # Check completed games
    completed = [g for g in regular_season if g.status in ['FINAL', 'OFF']]
    print(f'\nCompleted regular season games: {len(completed)}')

db.close()
