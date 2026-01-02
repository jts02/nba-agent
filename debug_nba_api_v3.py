#!/usr/bin/env python3
"""
Debug V3 API structure
"""
from nba_api.stats.endpoints import boxscoretraditionalv3, scoreboardv2
from datetime import datetime

print("=" * 70)
print("NBA API V3 STRUCTURE DEBUG")
print("=" * 70)

game_id = "0022500471"  # HOU @ BKN

print(f"\nFetching box score for game {game_id}...")

try:
    # Try V3
    box_score = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
    
    # Check what methods are available
    print("\nAvailable methods on box_score object:")
    methods = [m for m in dir(box_score) if not m.startswith('_') and callable(getattr(box_score, m))]
    for method in methods[:20]:  # Show first 20
        print(f"   - {method}")
    
    # Try different data access methods
    print("\n1. Trying get_normalized_dict()...")
    try:
        data = box_score.get_normalized_dict()
        print(f"   Keys: {list(data.keys()) if data else 'None/Empty'}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Trying get_dict()...")
    try:
        data = box_score.get_dict()
        print(f"   Keys: {list(data.keys()) if data else 'None/Empty'}")
        if data and 'resultSets' in data:
            print(f"   resultSets found: {len(data['resultSets'])} sets")
            for i, rs in enumerate(data['resultSets']):
                print(f"      Set {i}: {rs.get('name', 'unknown')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Trying get_data_frames()...")
    try:
        dfs = box_score.get_data_frames()
        print(f"   Number of DataFrames: {len(dfs)}")
        for i, df in enumerate(dfs):
            print(f"      DataFrame {i}: {len(df)} rows, columns: {list(df.columns)[:5]}...")
            if not df.empty:
                print(f"         Sample: {df.head(1).to_dict('records')}")
    except Exception as e:
        print(f"   Error: {e}")
        
except Exception as e:
    print(f"❌ Error creating box score object: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("CHECKING SCOREBOARD FOR ALL GAMES")
print("=" * 70)

# Check what games are available today
today = datetime.now().strftime("%Y-%m-%d")
print(f"\nFetching games for {today}...")

try:
    scoreboard = scoreboardv2.ScoreboardV2(game_date=today)
    games_data = scoreboard.get_normalized_dict()
    
    if 'GameHeader' in games_data:
        print(f"\n✅ Found {len(games_data['GameHeader'])} games:")
        for game in games_data['GameHeader']:
            status = game.get('GAME_STATUS_TEXT', 'Unknown')
            home = game.get('HOME_TEAM_ID')
            away = game.get('VISITOR_TEAM_ID')
            game_id = game.get('GAME_ID')
            print(f"   Game {game_id}: Status={status}, Teams={away}@{home}")
    else:
        print("❌ No GameHeader found")
        print(f"Available keys: {list(games_data.keys())}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)

