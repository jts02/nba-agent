#!/usr/bin/env python3
"""
MCP Server for Controversial Miami Heat Fan Bot
Tracks live Heat games and provides tools for hot takes
"""
import asyncio
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from loguru import logger

from clients import NBAClient, TwitterClient
from database import DatabaseManager
from config import settings
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from database.models import Base

# Initialize MCP Server
mcp = FastMCP("Heat-Fan-Server")

# Initialize clients
nba_client = NBAClient()
twitter_client = TwitterClient()
db_manager = DatabaseManager(settings.DATABASE_URL)


# New database model for tracking live game snapshots
class LiveGameSnapshot(Base):
    """Tracks box score snapshots during live games for comparison"""
    __tablename__ = "live_game_snapshots"
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String(50), nullable=False, index=True)
    snapshot_time = Column(DateTime, default=datetime.utcnow)
    period = Column(Integer)  # Quarter
    game_clock = Column(String(20))  # Time remaining
    heat_score = Column(Integer)
    opponent_score = Column(Integer)
    box_score_json = Column(Text)  # Full box score as JSON
    tweet_posted = Column(Boolean, default=False)
    tweet_id = Column(String(50), nullable=True)
    tweet_text = Column(Text, nullable=True)  # Store tweet content for similarity checking


# Create tables
db_manager.create_tables()
Base.metadata.create_all(bind=db_manager.engine)


@mcp.tool()
async def get_live_heat_game() -> Dict[str, Any]:
    """
    Check if Miami Heat have a game in progress RIGHT NOW.
    Returns game info if live, empty dict if no live game.
    """
    from nba_api.live.nba.endpoints import scoreboard
    
    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()
        
        # Look for Heat game (team_id: 1610612748)
        heat_team_id = 1610612748
        
        for game in games:
            home_team_id = game.get('homeTeam', {}).get('teamId')
            away_team_id = game.get('awayTeam', {}).get('teamId')
            game_status = game.get('gameStatus', 0)
            
            # gameStatus: 1 = scheduled, 2 = live, 3 = finished
            is_heat_game = (home_team_id == heat_team_id or away_team_id == heat_team_id)
            is_live = game_status == 2
            
            if is_heat_game and is_live:
                is_home = home_team_id == heat_team_id
                
                return {
                    "live": True,
                    "game_id": game.get('gameId'),
                    "period": game.get('period'),
                    "game_clock": game.get('gameClock'),
                    "heat_is_home": is_home,
                    "heat_team": "MIA",
                    "opponent_team": game.get('awayTeam', {}).get('teamTricode') if is_home else game.get('homeTeam', {}).get('teamTricode'),
                    "heat_score": game.get('homeTeam', {}).get('score') if is_home else game.get('awayTeam', {}).get('score'),
                    "opponent_score": game.get('awayTeam', {}).get('score') if is_home else game.get('homeTeam', {}).get('score'),
                }
        
        return {
            "live": False,
            "message": "No live Heat game right now"
        }
        
    except Exception as e:
        logger.error(f"Error checking live games: {e}")
        return {
            "live": False,
            "error": str(e)
        }


@mcp.tool()
async def get_heat_box_score(game_id: str) -> Dict[str, Any]:
    """
    Get current box score for a Heat game (uses LIVE API for in-progress games).
    Returns detailed player stats.
    
    Args:
        game_id: NBA game ID
    """
    try:
        from nba_api.live.nba.endpoints import boxscore as live_boxscore
        
        # Use LIVE box score API for in-progress games
        try:
            live_box = live_boxscore.BoxScore(game_id=game_id)
            game_data = live_box.game.get_dict()
            
            # Extract Heat players (team_id: 1610612748)
            heat_team_id = 1610612748
            heat_players = []
            
            # Check home team
            home_team = game_data.get('homeTeam', {})
            away_team = game_data.get('awayTeam', {})
            
            if home_team.get('teamId') == heat_team_id:
                players = home_team.get('players', [])
            elif away_team.get('teamId') == heat_team_id:
                players = away_team.get('players', [])
            else:
                return {"error": "Heat not in this game"}
            
            # Format player stats
            for player in players:
                stats = player.get('statistics', {})
                heat_players.append({
                    "player_name": player.get('name', 'Unknown'),
                    "player_id": player.get('personId'),
                    "position": player.get('position', ''),
                    "minutes": stats.get('minutes', '0:00'),
                    "points": stats.get('points', 0),
                    "rebounds": stats.get('reboundsTotal', 0),
                    "assists": stats.get('assists', 0),
                    "steals": stats.get('steals', 0),
                    "blocks": stats.get('blocks', 0),
                    "turnovers": stats.get('turnovers', 0),
                    "field_goals_made": stats.get('fieldGoalsMade', 0),
                    "field_goals_attempted": stats.get('fieldGoalsAttempted', 0),
                    "three_pointers_made": stats.get('threePointersMade', 0),
                    "three_pointers_attempted": stats.get('threePointersAttempted', 0),
                })
            
            return {
                "game_id": game_id,
                "heat_players": heat_players,
                "is_live": True,
                "period": game_data.get('period'),
                "game_clock": game_data.get('gameClock'),
            }
            
        except Exception as live_error:
            # If live API fails, try traditional API (for completed games)
            logger.warning(f"Live API failed, trying traditional: {live_error}")
            
            box_score = nba_client.get_box_score(game_id)
            if not box_score:
                return {"error": f"No box score found (live error: {live_error})"}
            
            team_stats = nba_client.get_all_players_stats(game_id)
            heat_team_id = 1610612748
            heat_players = team_stats.get(heat_team_id, [])
            
            return {
                "game_id": game_id,
                "heat_players": heat_players,
                "is_live": False,
                "source": "traditional_api"
            }
        
    except Exception as e:
        logger.error(f"Error getting box score: {e}")
        return {"error": str(e)}


@mcp.tool()
async def compare_box_scores(game_id: str, current_stats: List[Dict]) -> Dict[str, Any]:
    """
    Compare current box score to the last snapshot.
    Returns what changed for each Heat player.
    
    Args:
        game_id: NBA game ID
        current_stats: Current Heat player stats
    """
    session = db_manager.get_session()
    
    try:
        # Get most recent snapshot
        last_snapshot = (
            session.query(LiveGameSnapshot)
            .filter_by(game_id=game_id)
            .order_by(LiveGameSnapshot.snapshot_time.desc())
            .first()
        )
        
        if not last_snapshot:
            return {
                "first_check": True,
                "message": "No previous snapshot - this is the first check",
                "changes": []
            }
        
        # Parse old stats
        old_box_score = json.loads(last_snapshot.box_score_json)
        old_stats_by_player = {p['player_name']: p for p in old_box_score}
        
        # Compare each player
        changes = []
        for current_player in current_stats:
            name = current_player['player_name']
            old_player = old_stats_by_player.get(name)
            
            if not old_player:
                # New player entered the game
                changes.append({
                    "player": name,
                    "event": "entered_game",
                    "current_stats": current_player
                })
                continue
            
            # Check for changes in key stats
            pts_diff = current_player['points'] - old_player['points']
            fgm_diff = current_player.get('field_goals_made', 0) - old_player.get('field_goals_made', 0)
            fga_diff = current_player.get('field_goals_attempted', 0) - old_player.get('field_goals_attempted', 0)
            reb_diff = current_player['rebounds'] - old_player['rebounds']
            ast_diff = current_player['assists'] - old_player['assists']
            to_diff = current_player['turnovers'] - old_player['turnovers'] 
            
            if any([pts_diff, fgm_diff, fga_diff, reb_diff, ast_diff, to_diff]):
                changes.append({
                    "player": name,
                    "points_change": pts_diff,
                    "fgm_change": fgm_diff,
                    "fga_change": fga_diff,
                    "rebounds_change": reb_diff,
                    "assists_change": ast_diff,
                    "turnovers_change": to_diff,
                    "missed_shots": fga_diff - fgm_diff,  # Important for roasting!
                    "current_points": current_player['points'],
                    "current_rebounds": current_player['rebounds'],
                    "current_assists": current_player['assists'],
                })
        
        return {
            "first_check": False,
            "minutes_since_last": (datetime.utcnow() - last_snapshot.snapshot_time).seconds // 60,
            "changes": changes,
            "heat_score_change": None,  # Will add if needed
        }
        
    except Exception as e:
        logger.error(f"Error comparing box scores: {e}")
        return {"error": str(e)}
    finally:
        session.close()


@mcp.tool()
async def save_snapshot(
    game_id: str,
    period: int,
    game_clock: str,
    heat_score: int,
    opponent_score: int,
    heat_stats: List[Dict]
) -> Dict[str, Any]:
    """
    Save current game state for future comparison.
    
    Args:
        game_id: NBA game ID
        period: Current quarter
        game_clock: Time remaining
        heat_score: Heat's current score
        opponent_score: Opponent's score
        heat_stats: List of Heat player stats
    """
    session = db_manager.get_session()
    
    try:
        snapshot = LiveGameSnapshot(
            game_id=game_id,
            snapshot_time=datetime.utcnow(),
            period=period,
            game_clock=game_clock,
            heat_score=heat_score,
            opponent_score=opponent_score,
            box_score_json=json.dumps(heat_stats),
            tweet_posted=False
        )
        
        session.add(snapshot)
        session.commit()
        
        return {
            "success": True,
            "snapshot_id": snapshot.id,
            "saved_at": str(snapshot.snapshot_time)
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving snapshot: {e}")
        return {"error": str(e)}
    finally:
        session.close()


def calculate_tweet_similarity(tweet1: str, tweet2: str) -> float:
    """
    Calculate similarity between two tweets (0.0 to 1.0).
    Checks for overlapping player names, keywords, and sentiment.
    """
    # Normalize both tweets
    t1 = tweet1.upper()
    t2 = tweet2.upper()
    
    # Extract key phrases and player names
    keywords = ['BRICK', 'PERFECT', 'TRADE', 'BENCH', 'FIRE', 'HOT', 'COLD', 
                'MISS', 'MAKE', '0 PTS', '0 REBS', 'GOAT', 'TRASH', 'CLOWN',
                'FROM 3', 'FROM THREE', 'SHOOTING', 'POINTS', 'REBOUNDS']
    
    # Common Heat player last names and nicknames
    players = ['BAM', 'ADEBAYO', 'ADE-BRICK', 'JIMMY', 'BUTLER', 'TYLER', 'HERRO', 
               'HER-NO', 'NORMAN', 'POWELL', 'NORM', 'JOVIC', 'HIGHSMITH', 'ROBINSON', 
               'ROZIER', 'MARTIN', 'WARE', 'NIKOLA']
    
    # Count overlapping keywords
    t1_keywords = [k for k in keywords if k in t1]
    t2_keywords = [k for k in keywords if k in t2]
    keyword_overlap = len(set(t1_keywords) & set(t2_keywords))
    keyword_total = len(set(t1_keywords) | set(t2_keywords))
    
    # Count overlapping player names
    t1_players = [p for p in players if p in t1]
    t2_players = [p for p in players if p in t2]
    player_overlap = len(set(t1_players) & set(t2_players))
    player_total = len(set(t1_players) | set(t2_players))
    
    # Calculate similarity score
    if keyword_total == 0 and player_total == 0:
        return 0.0
    
    keyword_sim = keyword_overlap / keyword_total if keyword_total > 0 else 0
    player_sim = player_overlap / player_total if player_total > 0 else 0
    
    # If same player(s) AND similar sentiment keywords, boost similarity
    if player_overlap > 0 and keyword_overlap > 0:
        # Boost for same player + same sentiment
        boost = 0.2
        similarity = min(1.0, (player_sim * 0.6) + (keyword_sim * 0.4) + boost)
    else:
        # Weighted average (players matter more)
        similarity = (player_sim * 0.6) + (keyword_sim * 0.4)
    
    return similarity


@mcp.tool()
async def post_heat_tweet(tweet_text: str, game_id: str, snapshot_id: int) -> Dict[str, Any]:
    """
    Post a controversial Heat fan tweet.
    Checks for similarity with recent tweets to avoid repetition.
    
    Args:
        tweet_text: The spicy take to post
        game_id: NBA game ID
        snapshot_id: Database snapshot ID
    """
    session = db_manager.get_session()
    
    try:
        from datetime import timedelta
        
        # Check for similar tweets posted today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        todays_tweets = (
            session.query(LiveGameSnapshot)
            .filter(
                LiveGameSnapshot.tweet_posted == True,
                LiveGameSnapshot.snapshot_time >= today_start
            )
            .all()
        )
        
        # Check similarity with each tweet from today
        for old_snapshot in todays_tweets:
            if not old_snapshot.tweet_text:
                continue
            
            similarity = calculate_tweet_similarity(tweet_text, old_snapshot.tweet_text)
            
            # If similarity is too high (> 60%), reject the tweet
            if similarity > 0.6:
                logger.warning(f"Tweet too similar ({similarity:.2f}) to earlier tweet: {old_snapshot.tweet_text[:50]}...")
                return {
                    "success": False,
                    "error": f"Tweet too similar to earlier tweet today (similarity: {similarity:.2f})",
                    "similar_to": old_snapshot.tweet_text,
                    "similarity_score": similarity,
                    "blocked": True
                }
        
        # Post to Twitter
        tweet_id = twitter_client.post_tweet(tweet_text)
        
        if not tweet_id:
            return {
                "success": False,
                "error": "Failed to post tweet"
            }
        
        # Mark snapshot as tweeted AND store tweet text
        snapshot = session.query(LiveGameSnapshot).filter_by(id=snapshot_id).first()
        if snapshot:
            snapshot.tweet_posted = True
            snapshot.tweet_id = tweet_id
            snapshot.tweet_text = tweet_text  # Store for future similarity checks
            session.commit()
        
        return {
            "success": True,
            "tweet_id": tweet_id,
            "tweet_text": tweet_text
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error posting tweet: {e}")
        return {"error": str(e)}
    finally:
        session.close()


@mcp.tool()
async def check_recent_heat_tweets(game_id: str, minutes: int = 5) -> Dict[str, Any]:
    """
    Check if we've tweeted about this game recently.
    Prevents spam.
    
    Args:
        game_id: NBA game ID
        minutes: Don't tweet if we posted within this many minutes
    """
    session = db_manager.get_session()
    
    try:
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        recent_tweet = (
            session.query(LiveGameSnapshot)
            .filter_by(game_id=game_id, tweet_posted=True)
            .filter(LiveGameSnapshot.snapshot_time >= cutoff_time)
            .order_by(LiveGameSnapshot.snapshot_time.desc())
            .first()
        )
        
        if recent_tweet:
            return {
                "recently_tweeted": True,
                "minutes_ago": (datetime.utcnow() - recent_tweet.snapshot_time).seconds // 60,
                "tweet_id": recent_tweet.tweet_id
            }
        
        return {
            "recently_tweeted": False,
            "message": "Clear to tweet"
        }
        
    finally:
        session.close()


if __name__ == "__main__":
    mcp.run()

