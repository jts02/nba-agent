#!/usr/bin/env python3
"""
MCP Server for NBA Agent - Exposes NBA data and Twitter posting to AI agents.

This allows LangChain or other AI clients to interact with your NBA bot.
"""
import asyncio
from typing import Optional, List, Dict, Any
import json
from mcp.server.fastmcp import FastMCP

from clients import NBAClient, TwitterClient
from analyzers import BoxScoreFormatter
from database import DatabaseManager, BoxScorePost
from config import settings

# Initialize MCP Server
mcp = FastMCP("NBA-Agent-Server")

# Initialize clients
nba_client = NBAClient()
twitter_client = TwitterClient()
db_manager = DatabaseManager(settings.DATABASE_URL)
db_manager.create_tables()
formatter = BoxScoreFormatter()


@mcp.tool()
async def get_completed_games_today() -> List[Dict[str, Any]]:
    """
    Fetches all completed NBA games from today.
    Returns a list of games with scores and team names.
    """
    games = nba_client.get_completed_games_today()
    return games


@mcp.tool()
async def get_game_box_score(game_id: str) -> Dict[str, Any]:
    """
    Fetches detailed box score for a specific game.
    Includes all player stats (points, rebounds, assists, etc).
    
    Args:
        game_id: NBA game ID (e.g., "0022500471")
    """
    box_score = nba_client.get_box_score(game_id)
    
    if not box_score:
        return {"error": f"No box score found for game {game_id}"}
    
    return box_score


@mcp.tool()
async def format_game_tweet(game_id: str) -> str:
    """
    Formats a game into a tweet-ready format with top performers.
    Shows leading scorers, double-doubles, triple-doubles, and notable stats.
    
    Args:
        game_id: NBA game ID
    """
    # Get game info
    games = nba_client.get_completed_games_today()
    game = next((g for g in games if g['game_id'] == game_id), None)
    
    if not game:
        return f"Error: Game {game_id} not found in today's completed games"
    
    # Get detailed stats
    team_stats = nba_client.get_all_players_stats(game_id)
    
    if team_stats:
        tweet_text = formatter.format_game_with_top_performers(game, team_stats)
    else:
        tweet_text = formatter.format_game_summary(game)
    
    return tweet_text


@mcp.tool()
async def generate_custom_tweet(game_id: str, style: str = "exciting") -> str:
    """
    Generate a custom tweet for a game using AI-style formatting.
    Returns JUST the tweet text (no posting) - Claude can then decide whether to post it.
    
    Args:
        game_id: NBA game ID
        style: Style of tweet - "exciting", "stats_focused", "narrative", "hype"
        
    Returns:
        Generated tweet text (max 280 chars)
    """
    # Get game info
    games = nba_client.get_completed_games_today()
    game = next((g for g in games if g['game_id'] == game_id), None)
    
    if not game:
        return f"Error: Game {game_id} not found"
    
    # Get detailed stats
    team_stats = nba_client.get_all_players_stats(game_id)
    
    if not team_stats:
        return formatter.format_game_summary(game)
    
    # Analyze the game
    away_team = game['away_team']
    home_team = game['home_team']
    away_score = game.get('away_score', 0)
    home_score = game.get('home_score', 0)
    
    # Find top performers
    all_performances = []
    for team_id, players in team_stats.items():
        team_name = away_team if team_id == game.get('away_team_id') else home_team
        for player in players:
            perf = {
                'name': player['player_name'],
                'team': team_name,
                'pts': player['points'],
                'reb': player['rebounds'],
                'ast': player['assists'],
                'stl': player['steals'],
                'blk': player['blocks']
            }
            # Check for double-double/triple-double
            double_digit = sum(1 for stat in [perf['pts'], perf['reb'], perf['ast']] if stat >= 10)
            perf['double_double'] = double_digit >= 2
            perf['triple_double'] = double_digit >= 3
            all_performances.append(perf)
    
    # Sort by points
    top_performers = sorted(all_performances, key=lambda x: x['pts'], reverse=True)[:3]
    
    # Return structured data that Claude can format
    summary = {
        'matchup': f"{away_team} {away_score} @ {home_team} {home_score}",
        'winner': away_team if away_score > home_score else home_team,
        'margin': abs(away_score - home_score),
        'top_performers': [
            f"{p['name']} ({p['team']}): {p['pts']}p/{p['reb']}r/{p['ast']}a" +
            (" 🔥TRIPLE-DOUBLE" if p['triple_double'] else " 💪DD" if p['double_double'] else "")
            for p in top_performers
        ]
    }
    
    return json.dumps(summary, indent=2)


@mcp.tool()
async def post_custom_tweet(game_id: str, tweet_text: str) -> Dict[str, Any]:
    """
    Post a custom tweet that Claude has crafted.
    This separates tweet generation from posting, giving Claude full creative control.
    
    Args:
        game_id: NBA game ID (for database tracking)
        tweet_text: The tweet text to post (Claude generates this)
        
    Returns:
        Success status and tweet_id
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
        
        # Get game info for database
        games = nba_client.get_completed_games_today()
        game = next((g for g in games if g['game_id'] == game_id), None)
        
        if not game:
            return {
                "success": False,
                "error": f"Game {game_id} not found"
            }
        
        # Post to Twitter
        tweet_id = twitter_client.post_tweet(tweet_text)
        
        if not tweet_id:
            return {
                "success": False,
                "error": "Failed to post to Twitter"
            }
        
        # Save to database
        from datetime import datetime
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
        
        return {
            "success": True,
            "tweet_id": tweet_id,
            "game_id": game_id
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        session.close()


@mcp.tool()
async def post_game_to_twitter(game_id: str) -> Dict[str, Any]:
    """
    Posts a game's box score to Twitter with detailed stats.
    Checks database to avoid duplicate posts.
    
    Args:
        game_id: NBA game ID to post
        
    Returns:
        Dictionary with success status and tweet_id if posted
    """
    session = db_manager.get_session()
    
    try:
        # Check if already posted
        existing = session.query(BoxScorePost).filter_by(game_id=game_id).first()
        if existing:
            return {
                "success": False,
                "error": "Already posted",
                "tweet_id": existing.tweet_id,
                "posted_at": str(existing.posted_at)
            }
        
        # Get game info
        games = nba_client.get_completed_games_today()
        game = next((g for g in games if g['game_id'] == game_id), None)
        
        if not game:
            return {
                "success": False,
                "error": f"Game {game_id} not found in today's completed games"
            }
        
        # Format tweet
        team_stats = nba_client.get_all_players_stats(game_id)
        if team_stats:
            tweet_text = formatter.format_game_with_top_performers(game, team_stats)
        else:
            tweet_text = formatter.format_game_summary(game)
        
        # Post to Twitter
        tweet_id = twitter_client.post_tweet(tweet_text)
        
        if not tweet_id:
            return {
                "success": False,
                "error": "Failed to post to Twitter"
            }
        
        # Save to database
        from datetime import datetime
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
        
        return {
            "success": True,
            "tweet_id": tweet_id,
            "game_id": game_id,
            "tweet_text": tweet_text
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        session.close()


@mcp.tool()
async def get_posted_games() -> List[Dict[str, Any]]:
    """
    Gets all games that have been posted to Twitter.
    Returns game IDs, teams, scores, and tweet IDs.
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
    Checks for completed games that haven't been posted yet.
    Returns list of game IDs that are ready to post.
    """
    session = db_manager.get_session()
    
    try:
        # Get all completed games
        games = nba_client.get_completed_games_today()
        
        # Filter out already posted
        new_games = []
        for game in games:
            existing = session.query(BoxScorePost).filter_by(game_id=game['game_id']).first()
            if not existing:
                new_games.append({
                    "game_id": game['game_id'],
                    "matchup": f"{game['away_team']} @ {game['home_team']}",
                    "score": f"{game.get('away_score', 0)} - {game.get('home_score', 0)}"
                })
        
        return {
            "total_completed": len(games),
            "already_posted": len(games) - len(new_games),
            "new_games": new_games
        }
    finally:
        session.close()


if __name__ == "__main__":
    # MCP servers run over stdio (Standard Input/Output)
    # This allows an LLM client (like Claude via LangChain) to communicate
    mcp.run()

