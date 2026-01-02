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
        
        # Try to get top performers
        print(f"Fetching detailed stats for game {game['game_id']}...")
        top_performers = nba.get_top_performers(game['game_id'], top_n=1)
        
        # Format the tweet
        if top_performers:
            tweet_text = formatter.format_game_with_top_performers(game, top_performers)
        else:
            tweet_text = formatter.format_game_summary(game)
        
        # Display the formatted tweet
        print("\nFormatted tweet:")
        print("-" * 60)
        print(tweet_text)
        print("-" * 60)
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
            top_performers = nba.get_top_performers(game['game_id'], top_n=1)
            if top_performers:
                tweet_text = formatter.format_game_with_top_performers(game, top_performers)
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

