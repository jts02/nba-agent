#!/usr/bin/env python3
"""
Test game status detection from box score meta field
"""
from nba_api.stats.endpoints import boxscoretraditionalv3, scoreboardv2
from datetime import datetime

print("=" * 70)
print("GAME STATUS DETECTION TEST")
print("=" * 70)

# Get all games from today
today = datetime.now().strftime("%Y-%m-%d")
print(f"\nFetching games for {today}...")

scoreboard = scoreboardv2.ScoreboardV2(game_date=today)
games_data = scoreboard.get_normalized_dict()

if 'GameHeader' in games_data:
    games = games_data['GameHeader']
    print(f"\n✅ Found {len(games)} games\n")
    
    for game in games:
        game_id = game['GAME_ID']
        scoreboard_status = game['GAME_STATUS_TEXT']
        
        print(f"{'='*70}")
        print(f"Game ID: {game_id}")
        print(f"Scoreboard status: '{scoreboard_status}'")
        
        # Try to get box score meta
        try:
            box_score = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
            response = box_score.get_dict()
            
            if 'meta' in response:
                meta = response['meta']
                box_status = meta.get('gameStatusText', 'Unknown')
                period = meta.get('period', None)
                
                print(f"Box score status: '{box_status}'")
                print(f"Period: {period}")
                
                # Check if game is done
                if box_status.lower() == 'final':
                    print("✅ GAME IS COMPLETE (from box score meta)")
                elif scoreboard_status.strip().lower() == 'final':
                    print("✅ GAME IS COMPLETE (from scoreboard)")
                else:
                    print(f"⏳ Game is ongoing (period {period})")
            else:
                print("❌ No meta field in box score response")
                
        except Exception as e:
            print(f"❌ Error fetching box score: {e}")
        
        print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
Recommendation:
- Use scoreboard status first (GAME_STATUS_TEXT == 'Final')
- This is more reliable and doesn't require extra API calls
- Box score meta can be used as backup if needed
""")

