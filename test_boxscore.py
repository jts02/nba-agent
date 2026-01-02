#!/usr/bin/env python3
"""
Test script to manually check and display NBA box scores.
This is useful for testing without waiting for the scheduler.
"""
from clients import TwitterClient, NBAClient
from analyzers import BoxScoreFormatter
from config import settings


def main():
    """Test box score fetching and formatting."""
    print("=" * 60)
    print("NBA Box Score Test")
    print("=" * 60)
    
    # Initialize clients
    print("\nInitializing clients...")
    nba = NBAClient()
    formatter = BoxScoreFormatter()
    
    # Get completed games from today
    print("Fetching completed games from today...")
    games = nba.get_completed_games_today()
    
    if not games:
        print("\n❌ No completed games found today.")
        print("   (This is normal if no games have finished yet)")
        return
    
    print(f"\n✅ Found {len(games)} completed game(s):\n")
    
    # Display each game
    for i, game in enumerate(games, 1):
        print(f"\n{'='*60}")
        print(f"Game {i}: {game['away_team']} @ {game['home_team']}")
        print('='*60)
        
        # Try to get detailed player stats
        print(f"\nFetching detailed stats for game {game['game_id']}...")
        team_stats = nba.get_all_players_stats(game['game_id'])
        
        # Debug: Show what we got
        if team_stats:
            print(f"✅ Got stats for {len(team_stats)} teams")
            for team_id, players in team_stats.items():
                print(f"   Team {team_id}: {len(players)} players")
                # Show top 3 scorers
                top_3 = sorted(players, key=lambda x: x['points'], reverse=True)[:3]
                for player in top_3:
                    print(f"      {player['player_name']}: {player['points']}pts/"
                          f"{player['rebounds']}reb/{player['assists']}ast")
        else:
            print("❌ No detailed stats available")
        
        # Format the tweet with detailed stats
        print("\n" + "="*60)
        print("TWEET THAT WOULD BE POSTED:")
        print("="*60)
        
        if team_stats:
            tweet_text = formatter.format_game_with_top_performers(game, team_stats)
        else:
            print("⚠️  Using fallback format (no detailed stats)")
            tweet_text = formatter.format_game_summary(game)
        
        # Display the formatted tweet
        print(tweet_text)
        print("="*60)
        print(f"Length: {len(tweet_text)} characters")
        
        # Show game details
        print(f"\nGame Details:")
        print(f"  Game ID: {game['game_id']}")
        print(f"  Date: {game['game_date']}")
        print(f"  Score: {game['away_team']} {game.get('away_score', 'N/A')} - "
              f"{game['home_team']} {game.get('home_score', 'N/A')}")
    
    # Ask if user wants to post
    print("\n" + "=" * 60)
    response = input("\nDo you want to post these to Twitter? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nPosting to Twitter...")
        twitter = TwitterClient()
        
        for game in games:
            # Get formatted tweet again
            team_stats = nba.get_all_players_stats(game['game_id'])
            if team_stats:
                tweet_text = formatter.format_game_with_top_performers(game, team_stats)
            else:
                tweet_text = formatter.format_game_summary(game)
            
            # Post it
            tweet_id = twitter.post_tweet(tweet_text)
            
            if tweet_id:
                print(f"✅ Posted game {game['game_id']} as tweet {tweet_id}")
            else:
                print(f"❌ Failed to post game {game['game_id']}")
    else:
        print("\n Skipping Twitter posting.")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

