#!/usr/bin/env python3
"""
Test script to manually check and display NBA box scores.
This is useful for testing without waiting for the scheduler.
"""
from clients import TwitterClient, NBAClient
from analyzers import BoxScoreFormatter
from config import settings
from database import DatabaseManager, BoxScorePost
from datetime import datetime


def main():
    """Test box score fetching and formatting."""
    print("=" * 60)
    print("NBA Box Score Test")
    print("=" * 60)
    
    # Initialize clients and database
    print("\nInitializing clients and database...")
    nba = NBAClient()
    formatter = BoxScoreFormatter()
    db_manager = DatabaseManager(settings.DATABASE_URL)
    db_manager.create_tables()
    
    session = db_manager.get_session()
    
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
        
        # Check if already posted
        game_id = game['game_id']
        existing = session.query(BoxScorePost).filter_by(game_id=game_id).first()
        
        if existing:
            print(f"⚠️  This game was already posted on {existing.posted_at}")
            print(f"   Tweet ID: {existing.tweet_id}")
            print(f"   Skipping to avoid duplicate...")
            continue
        
        # Try to get detailed player stats
        print(f"\nFetching detailed stats for game {game_id}...")
        team_stats = nba.get_all_players_stats(game_id)
        
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
        
        try:
            for game in games:
                game_id = game['game_id']
                
                # Skip if already posted (check again in case multiple games)
                existing = session.query(BoxScorePost).filter_by(game_id=game_id).first()
                if existing:
                    print(f"⏭️  Skipping game {game_id} (already posted)")
                    continue
                
                # Get formatted tweet
                team_stats = nba.get_all_players_stats(game_id)
                if team_stats:
                    tweet_text = formatter.format_game_with_top_performers(game, team_stats)
                else:
                    tweet_text = formatter.format_game_summary(game)
                
                # Post it
                tweet_id = twitter.post_tweet(tweet_text)
                
                if tweet_id:
                    print(f"✅ Posted game {game_id} as tweet {tweet_id}")
                    
                    # Save to database
                    box_score_post = BoxScorePost(
                        game_id=game_id,
                        game_date=datetime.strptime(game['game_date'], "%Y-%m-%dT%H:%M:%S"),
                        home_team=game['home_team'],
                        away_team=game['away_team'],
                        home_score=game.get('home_score', 0),
                        away_score=game.get('away_score', 0),
                        post_text=tweet_text,
                        tweet_id=tweet_id,
                        posted_at=datetime.utcnow()
                    )
                    session.add(box_score_post)
                    session.commit()
                    print(f"   💾 Saved to database")
                else:
                    print(f"❌ Failed to post game {game_id}")
            
            print("\n✅ All new games posted!")
            
        except Exception as e:
            print(f"\n❌ Error during posting: {e}")
            session.rollback()
        finally:
            session.close()
    else:
        print("\n⏭️  Skipping Twitter posting.")
        session.close()
    
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

