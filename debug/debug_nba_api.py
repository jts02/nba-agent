#!/usr/bin/env python3
"""
Debug script to test NBA API box score fetching.
"""
from nba_api.stats.endpoints import boxscoretraditionalv3
from clients import NBAClient

print("=" * 70)
print("NBA API DEBUG")
print("=" * 70)

# Get today's games
print("\n1. Fetching today's completed games...")
nba = NBAClient()
games = nba.get_completed_games_today()

if not games:
    print("❌ No completed games found")
    exit(1)

print(f"✅ Found {len(games)} completed game(s)")

for game in games:
    print(f"\n{'='*70}")
    print(f"Game: {game['away_team']} @ {game['home_team']}")
    print(f"Game ID: {game['game_id']}")
    print(f"Score: {game.get('away_score', 'N/A')} - {game.get('home_score', 'N/A')}")
    print('='*70)
    
    # Try to fetch box score directly
    print(f"\n2. Fetching box score for game {game['game_id']}...")
    
    try:
        box_score = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game['game_id'])
        data = box_score.get_normalized_dict()
        
        print(f"✅ API call successful!")
        print(f"   Available keys: {list(data.keys())}")
        
        if 'PlayerStats' in data:
            player_stats = data['PlayerStats']
            print(f"   ✅ PlayerStats found: {len(player_stats)} entries")
            
            # Show first few players
            print("\n   Sample players:")
            for i, player in enumerate(player_stats[:5]):
                print(f"      {player.get('PLAYER_NAME', 'Unknown')}: "
                      f"{player.get('PTS', 0)}pts/{player.get('REB', 0)}reb/"
                      f"{player.get('AST', 0)}ast")
            
            # Group by team
            teams = {}
            for player in player_stats:
                team_id = player.get('TEAM_ID')
                if team_id not in teams:
                    teams[team_id] = []
                teams[team_id].append(player)
            
            print(f"\n   Teams found: {len(teams)}")
            for team_id, players in teams.items():
                print(f"      Team {team_id}: {len(players)} players")
                # Show top scorer
                if players:
                    top_scorer = max(players, key=lambda x: x.get('PTS', 0))
                    print(f"         Top scorer: {top_scorer.get('PLAYER_NAME')}"
                          f" - {top_scorer.get('PTS')}pts")
        else:
            print("   ❌ No PlayerStats key found")
            print(f"   Available data keys: {list(data.keys())}")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)

