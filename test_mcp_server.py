#!/usr/bin/env python3
"""
Test MCP Server - Uses dummy game data instead of real NBA API.

Run with: python ai_agent.py test
"""
import json
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP

from clients import TwitterClient
from database import DatabaseManager, BoxScorePost
from config import settings

# Initialize MCP Server
mcp = FastMCP("NBA-Agent-Test-Server")

# Initialize clients (Twitter still real, NBA data is fake)
twitter_client = TwitterClient()
db_manager = DatabaseManager(settings.DATABASE_URL)
db_manager.create_tables()

# Load test data
with open("test_data.json", "r") as f:
    test_data = json.load(f)


@mcp.tool()
async def get_completed_games_today() -> List[Dict[str, Any]]:
    """
    Returns test games from test_data.json.
    """
    games = []
    for game_data in test_data["games"]:
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
async def get_game_box_score(game_id: str) -> Dict[str, Any]:
    """
    Returns test box score data for a game.
    """
    game_data = next((g for g in test_data["games"] if g["game_id"] == game_id), None)
    
    if not game_data:
        return {"error": f"Test game {game_id} not found"}
    
    # Convert to format expected by the system
    team_stats = {}
    for team_id, players in game_data["player_stats"].items():
        team_stats[int(team_id)] = players
    
    return {
        "game_id": game_id,
        "team_stats": team_stats,
    }


@mcp.tool()
async def format_game_tweet(game_id: str) -> str:
    """
    Formats a game into a tweet-ready format.
    """
    from analyzers import BoxScoreFormatter
    
    game_data = next((g for g in test_data["games"] if g["game_id"] == game_id), None)
    if not game_data:
        return f"Error: Test game {game_id} not found"
    
    game = {
        "game_id": game_id,
        "game_date": game_data["game_date"],
        "home_team": game_data["home_team"],
        "away_team": game_data["away_team"],
        "home_score": game_data["home_score"],
        "away_score": game_data["away_score"],
        "home_team_id": game_data["home_team_id"],
        "away_team_id": game_data["away_team_id"],
    }
    
    # Build team_stats from test data
    team_stats = {}
    for team_id, players in game_data["player_stats"].items():
        team_stats[int(team_id)] = players
    
    formatter = BoxScoreFormatter()
    if team_stats:
        tweet_text = formatter.format_game_with_top_performers(game, team_stats)
    else:
        tweet_text = formatter.format_game_summary(game)
    
    return tweet_text


@mcp.tool()
async def generate_custom_tweet(game_id: str, style: str = "exciting") -> str:
    """
    Generate custom tweet data for Claude to format.
    """
    game_data = next((g for g in test_data["games"] if g["game_id"] == game_id), None)
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
    """
    Post a custom tweet (uses real Twitter, but marks as test in database).
    """
    session = db_manager.get_session()
    
    try:
        # Check if already posted
        existing = session.query(BoxScorePost).filter_by(game_id=game_id).first()
        if existing:
            return {
                "success": False,
                "error": "Already posted",
                "tweet_id": existing.tweet_id
            }
        
        # Get game info
        game_data = next((g for g in test_data["games"] if g["game_id"] == game_id), None)
        if not game_data:
            return {"success": False, "error": f"Test game {game_id} not found"}
        
        # Post to Twitter (real posting!)
        tweet_id = twitter_client.post_tweet(tweet_text + "\n\n🧪 TEST POST")
        
        if not tweet_id:
            return {"success": False, "error": "Failed to post to Twitter"}
        
        # Save to database
        from datetime import datetime
        box_score_post = BoxScorePost(
            game_id=game_id,
            game_date=datetime.strptime(game_data["game_date"], "%Y-%m-%dT%H:%M:%S"),
            home_team=game_data["home_team"],
            away_team=game_data["away_team"],
            home_score=game_data["home_score"],
            away_score=game_data["away_score"],
            post_text=tweet_text,
            tweet_id=tweet_id,
            posted_at=datetime.utcnow()
        )
        session.add(box_score_post)
        session.commit()
        
        return {
            "success": True,
            "tweet_id": tweet_id,
            "game_id": game_id,
            "note": "TEST MODE - Tweet includes 'TEST POST' marker"
        }
        
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()


@mcp.tool()
async def post_game_to_twitter(game_id: str) -> Dict[str, Any]:
    """
    Post using old format (fallback).
    """
    # Use generate_custom_tweet and post_custom_tweet
    tweet_data = await generate_custom_tweet(game_id)
    # This is a simplified version - in practice Claude should use generate_custom_tweet + post_custom_tweet
    return await post_custom_tweet(game_id, "Test tweet")


@mcp.tool()
async def get_posted_games() -> List[Dict[str, Any]]:
    """
    Get all posted games from database.
    """
    session = db_manager.get_session()
    
    try:
        posts = session.query(BoxScorePost).order_by(BoxScorePost.posted_at.desc()).all()
        
        return [
            {
                "game_id": post.game_id,
                "home_team": post.home_team,
                "away_team": post.away_team,
                "home_score": post.home_score,
                "away_score": post.away_score,
                "tweet_id": post.tweet_id,
                "posted_at": str(post.posted_at)
            }
            for post in posts
        ]
    finally:
        session.close()


@mcp.tool()
async def check_for_new_games() -> Dict[str, Any]:
    """
    Check for test games that haven't been posted yet.
    """
    session = db_manager.get_session()
    
    try:
        all_games = test_data["games"]
        new_games = []
        
        for game_data in all_games:
            game_id = game_data["game_id"]
            existing = session.query(BoxScorePost).filter_by(game_id=game_id).first()
            if not existing:
                new_games.append({
                    "game_id": game_id,
                    "matchup": f"{game_data['away_team']} @ {game_data['home_team']}",
                    "score": f"{game_data.get('away_score', 0)} - {game_data.get('home_score', 0)}"
                })
        
        return {
            "total_completed": len(all_games),
            "already_posted": len(all_games) - len(new_games),
            "new_games": new_games,
            "note": "TEST MODE - Using dummy data"
        }
    finally:
        session.close()


if __name__ == "__main__":
    mcp.run()

