#!/usr/bin/env python3
"""
Combined Test MCP Server - Tests BOTH box scores and injuries with dummy data.

Run with: python ai_agent.py --test
"""
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from clients import TwitterClient
from database import DatabaseManager, BoxScorePost, ProcessedTweet
from config import settings

# Initialize MCP Server
mcp = FastMCP("NBA-Agent-Combined-Test-Server")

# Initialize clients
twitter_client = TwitterClient()
db_manager = DatabaseManager(settings.DATABASE_URL)
db_manager.create_tables()

# Load test data
with open("test_data.json", "r") as f:
    box_score_test_data = json.load(f)

with open("test_injury_data.json", "r") as f:
    injury_test_data = json.load(f)


# ============================================================
# BOX SCORE TOOLS (from test_mcp_server.py)
# ============================================================

@mcp.tool()
async def get_completed_games_today() -> List[Dict[str, Any]]:
    """Returns test games from test_data.json."""
    games = []
    for game_data in box_score_test_data["games"]:
        games.append({
            "game_id": game_data["game_id"],
            "game_date": game_data["game_date"],
            "home_team_id": game_data["home_team_id"],
            "away_team_id": game_data["away_team_id"],
            "home_team": game_data["home_team"],
            "away_team": game_data["away_team"],
            "home_score": game_data["home_score"],
            "away_score": game_data["away_score"],
        })
    return games


@mcp.tool()
async def generate_custom_tweet(game_id: str, style: str = "exciting") -> str:
    """Generate custom tweet data for Claude to format."""
    game_data = next((g for g in box_score_test_data["games"] if g["game_id"] == game_id), None)
    if not game_data:
        return json.dumps({"error": f"Test game {game_id} not found"})
    
    away_team = game_data["away_team"]
    home_team = game_data["home_team"]
    away_score = game_data["away_score"]
    home_score = game_data["home_score"]
    
    # Find top performers
    all_performances = []
    for team_id, players in game_data["player_stats"].items():
        team_name = away_team if team_id == str(game_data["away_team_id"]) else home_team
        for player in players:
            perf = {
                "name": player["player_name"],
                "team": team_name,
                "pts": player["points"],
                "reb": player["rebounds"],
                "ast": player["assists"],
                "stl": player["steals"],
                "blk": player["blocks"]
            }
            double_digit = sum(1 for stat in [perf["pts"], perf["reb"], perf["ast"]] if stat >= 10)
            perf["double_double"] = double_digit >= 2
            perf["triple_double"] = double_digit >= 3
            all_performances.append(perf)
    
    top_performers = sorted(all_performances, key=lambda x: x["pts"], reverse=True)[:3]
    
    summary = {
        "matchup": f"{away_team} {away_score} @ {home_team} {home_score}",
        "winner": away_team if away_score > home_score else home_team,
        "margin": abs(away_score - home_score),
        "top_performers": [
            f"{p['name']} ({p['team']}): {p['pts']}p/{p['reb']}r/{p['ast']}a" +
            (" 🔥TRIPLE-DOUBLE" if p["triple_double"] else " 💪DD" if p["double_double"] else "")
            for p in top_performers
        ]
    }
    
    return json.dumps(summary, indent=2)


@mcp.tool()
async def post_custom_tweet(game_id: str, tweet_text: str) -> Dict[str, Any]:
    """Post a custom tweet. In TEST MODE, only prints the tweet."""
    session = db_manager.get_session()
    
    try:
        # Check if already posted
        existing = session.query(BoxScorePost).filter_by(game_id=game_id).first()
        if existing:
            return {
                "success": False,
                "error": "Already posted",
                "tweet_id": existing.tweet_id,
                "note": "TEST MODE - Game already processed"
            }
        
        # Get game info
        game_data = next((g for g in box_score_test_data["games"] if g["game_id"] == game_id), None)
        if not game_data:
            return {"success": False, "error": f"Test game {game_id} not found"}
        
        # TEST MODE: Don't post to Twitter, just print
        print("\n" + "=" * 60)
        print("🧪 TEST MODE - Generated Tweet (NOT posted to Twitter):")
        print("=" * 60)
        print(tweet_text)
        print("=" * 60)
        print(f"Length: {len(tweet_text)} characters")
        print("=" * 60 + "\n")
        
        # Save to database
        box_score_post = BoxScorePost(
            game_id=game_id,
            game_date=datetime.strptime(game_data["game_date"], "%Y-%m-%dT%H:%M:%S"),
            home_team=game_data["home_team"],
            away_team=game_data["away_team"],
            home_score=game_data["home_score"],
            away_score=game_data["away_score"],
            post_text=tweet_text,
            tweet_id="TEST_MODE_NO_POST",
            posted_at=datetime.utcnow()
        )
        session.add(box_score_post)
        session.commit()
        
        return {
            "success": True,
            "tweet_id": "TEST_MODE_NO_POST",
            "game_id": game_id,
            "tweet_text": tweet_text,
            "note": "TEST MODE - Tweet generated but NOT posted to Twitter"
        }
        
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()


@mcp.tool()
async def check_for_new_games() -> Dict[str, Any]:
    """Check for test games that haven't been posted yet."""
    session = db_manager.get_session()
    
    try:
        games = box_score_test_data["games"]
        new_games = []
        
        for game_data in games:
            game_id = game_data["game_id"]
            existing = session.query(BoxScorePost).filter_by(game_id=game_id).first()
            if not existing:
                new_games.append({
                    "game_id": game_id,
                    "matchup": f"{game_data['away_team']} @ {game_data['home_team']}",
                    "score": f"{game_data.get('away_score', 0)} - {game_data.get('home_score', 0)}"
                })
        
        return {
            "total_completed": len(games),
            "already_posted": len(games) - len(new_games),
            "new_games": new_games,
            "note": "TEST MODE - Using dummy game data"
        }
    finally:
        session.close()


# ============================================================
# INJURY TOOLS (from test_injury_mcp_server.py)
# ============================================================

@mcp.tool()
async def get_recent_tweets(username: str = "ShamsCharania", max_results: int = 10) -> List[Dict[str, Any]]:
    """Get recent tweets from test data (simulates Twitter API)."""
    tweets = injury_test_data["tweets"][:max_results]
    return tweets


@mcp.tool()
async def analyze_tweet_for_injury(tweet_text: str) -> Dict[str, Any]:
    """Analyze a tweet for injury content. In test mode, uses keyword matching."""
    # Simple keyword-based detection
    injury_keywords = [
        "injury", "injured", "hurt", "sprain", "strain", "tear", "torn",
        "surgery", "MRI", "out", "miss", "questionable", "doubtful", "ruled out"
    ]
    
    text_lower = tweet_text.lower()
    keyword_count = sum(1 for keyword in injury_keywords if keyword in text_lower)
    
    is_injury = keyword_count >= 2
    confidence = min(0.9, 0.5 + (keyword_count * 0.15))
    
    return {
        "is_injury": is_injury,
        "confidence": confidence,
        "summary": f"Detected injury-related content (confidence: {confidence:.2f})"
    }


@mcp.tool()
async def post_injury_tweet(player_name: str, injury_type: str, time_missed: Optional[str] = None) -> Dict[str, Any]:
    """Post a tweet about a player injury. In TEST MODE, only prints."""
    # Format the injury tweet
    if time_missed:
        tweet_text = f"🏥 Injury Report: {player_name} - {injury_type}. Expected to miss {time_missed}."
    else:
        tweet_text = f"🏥 Injury Report: {player_name} - {injury_type}."
    
    # TEST MODE: Don't post to Twitter, just print
    print("\n" + "=" * 60)
    print("🧪 TEST MODE - Generated Injury Tweet (NOT posted):")
    print("=" * 60)
    print(tweet_text)
    print("=" * 60)
    print(f"Length: {len(tweet_text)} characters")
    print("=" * 60 + "\n")
    
    return {
        "success": True,
        "tweet_id": "TEST_MODE_INJURY",
        "tweet_text": tweet_text,
        "note": "TEST MODE - Tweet generated but NOT posted to Twitter"
    }


@mcp.tool()
async def check_and_post_injury_tweets(username: str = "ShamsCharania") -> Dict[str, Any]:
    """Check for new injury-related tweets. In TEST MODE, uses dummy data."""
    session = db_manager.get_session()
    
    try:
        tweets = injury_test_data["tweets"]
        
        injury_count = 0
        posted_count = 0
        processed_tweets = []
        
        for tweet_data in tweets:
            tweet_id = tweet_data['id']
            tweet_text = tweet_data['text']
            
            # Check if already processed
            existing = session.query(ProcessedTweet).filter_by(tweet_id=tweet_id).first()
            if existing:
                continue
            
            # Analyze for injury
            analysis = await analyze_tweet_for_injury(tweet_text)
            is_injury = analysis.get('is_injury', False)
            confidence = analysis.get('confidence', 0.0)
            
            # Create database record
            processed_tweet = ProcessedTweet(
                tweet_id=tweet_id,
                author_username=username,
                tweet_text=tweet_text,
                is_injury_related=is_injury,
                reposted=False,
                repost_id="TEST_MODE_NO_POST" if is_injury else None,
                processed_at=datetime.utcnow()
            )
            
            # If injury-related and high confidence, "post" it
            if is_injury and confidence >= 0.7:
                injury_count += 1
                
                # Extract simple info and post
                print(f"\n🏥 Found injury tweet: {tweet_text[:100]}...")
                processed_tweet.reposted = True
                processed_tweet.repost_id = "TEST_MODE_INJURY_POST"
                posted_count += 1
                
                processed_tweets.append({
                    "tweet_id": tweet_id,
                    "text": tweet_text[:100] + "...",
                    "posted": True
                })
            
            session.add(processed_tweet)
        
        session.commit()
        
        return {
            "new_tweets": len(tweets),
            "injury_tweets": injury_count,
            "posted": posted_count,
            "processed_tweets": processed_tweets,
            "message": f"TEST MODE: Processed {len(tweets)} tweets, found {injury_count} injuries, posted {posted_count}",
            "note": "TEST MODE - No actual tweets posted to Twitter"
        }
        
    except Exception as e:
        session.rollback()
        return {
            "error": str(e)
        }
    finally:
        session.close()


@mcp.tool()
async def get_processed_injury_tweets() -> List[Dict[str, Any]]:
    """Get all processed injury tweets from database."""
    session = db_manager.get_session()
    
    try:
        tweets = (
            session.query(ProcessedTweet)
            .filter_by(is_injury_related=True)
            .order_by(ProcessedTweet.processed_at.desc())
            .all()
        )
        
        return [
            {
                "tweet_id": tweet.tweet_id,
                "author": tweet.author_username,
                "text": tweet.tweet_text,
                "reposted": tweet.reposted,
                "repost_id": tweet.repost_id,
                "processed_at": str(tweet.processed_at)
            }
            for tweet in tweets
        ]
    finally:
        session.close()


if __name__ == "__main__":
    mcp.run()

