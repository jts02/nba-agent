#!/usr/bin/env python3
"""
TEST MCP Server for Heat Fan Bot
Uses dummy data to simulate a live Heat game
"""
import asyncio
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from loguru import logger

# Initialize MCP Server
mcp = FastMCP("Test-Heat-Fan-Server")

# Dummy game state that evolves over time
GAME_STATE = {
    "check_count": 0,
    "period": 2,
    "game_clock": "8:45",
    "heat_score": 48,
    "opponent_score": 52,
    "game_id": "0022500TEST",
    "opponent": "BOS",
}

# Dummy player stats that change each check
PLAYER_STATS = {
    "Bam Adebayo": {"points": 7, "rebounds": 8, "assists": 1, "fgm": 3, "fga": 5, "turnovers": 0},
    "Jimmy Butler": {"points": 15, "rebounds": 4, "assists": 5, "fgm": 6, "fga": 12, "turnovers": 2},
    "Tyler Herro": {"points": 8, "rebounds": 2, "assists": 2, "fgm": 3, "fga": 9, "turnovers": 0},
}

# Store last snapshot for comparison
LAST_SNAPSHOT = None


@mcp.tool()
async def get_live_heat_game() -> Dict[str, Any]:
    """Check if there's a live Heat game (always returns True in test mode)"""
    return {
        "live": True,
        "game_id": GAME_STATE["game_id"],
        "period": GAME_STATE["period"],
        "game_clock": GAME_STATE["game_clock"],
        "heat_is_home": True,
        "heat_team": "MIA",
        "opponent_team": GAME_STATE["opponent"],
        "heat_score": GAME_STATE["heat_score"],
        "opponent_score": GAME_STATE["opponent_score"],
    }


@mcp.tool()
async def get_heat_box_score(game_id: str) -> Dict[str, Any]:
    """Get current box score (returns evolving dummy data)"""
    global GAME_STATE, PLAYER_STATS
    
    # Evolve the game state based on check count
    GAME_STATE["check_count"] += 1
    check = GAME_STATE["check_count"]
    
    # Simulate different scenarios
    if check == 1:
        # First check - nothing special
        pass
    elif check == 2:
        # Bam misses 3 shots in a row (no points)
        PLAYER_STATS["Bam Adebayo"]["fga"] += 3
        PLAYER_STATS["Bam Adebayo"]["turnovers"] += 1
    elif check == 3:
        # Jimmy goes OFF - 10 points in 3 minutes
        PLAYER_STATS["Jimmy Butler"]["points"] += 10
        PLAYER_STATS["Jimmy Butler"]["fgm"] += 4
        PLAYER_STATS["Jimmy Butler"]["fga"] += 5
        GAME_STATE["heat_score"] += 10
    elif check == 4:
        # Tyler Herro can't hit anything
        PLAYER_STATS["Tyler Herro"]["fga"] += 5
        # No makes
    elif check == 5:
        # Bam redemption arc
        PLAYER_STATS["Bam Adebayo"]["points"] += 8
        PLAYER_STATS["Bam Adebayo"]["fgm"] += 4
        PLAYER_STATS["Bam Adebayo"]["fga"] += 4
        PLAYER_STATS["Bam Adebayo"]["rebounds"] += 4
    
    # Convert to expected format
    heat_players = []
    for name, stats in PLAYER_STATS.items():
        heat_players.append({
            "player_name": name,
            "points": stats["points"],
            "rebounds": stats["rebounds"],
            "assists": stats["assists"],
            "field_goals_made": stats["fgm"],
            "field_goals_attempted": stats["fga"],
            "turnovers": stats["turnovers"],
        })
    
    return {
        "game_id": game_id,
        "heat_players": heat_players,
        "message": f"TEST MODE - Check #{check}"
    }


@mcp.tool()
async def compare_box_scores(game_id: str, current_stats: List[Dict]) -> Dict[str, Any]:
    """Compare current to last snapshot"""
    global LAST_SNAPSHOT
    
    if LAST_SNAPSHOT is None:
        return {
            "first_check": True,
            "message": "No previous snapshot - this is the first check",
            "changes": []
        }
    
    # Compare
    old_stats_by_player = {p['player_name']: p for p in LAST_SNAPSHOT}
    
    changes = []
    for current_player in current_stats:
        name = current_player['player_name']
        old_player = old_stats_by_player.get(name)
        
        if not old_player:
            continue
        
        pts_diff = current_player['points'] - old_player['points']
        fgm_diff = current_player['field_goals_made'] - old_player['field_goals_made']
        fga_diff = current_player['field_goals_attempted'] - old_player['field_goals_attempted']
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
                "current_points": current_player['points'],
                "current_rebounds": current_player['rebounds'],
                "current_assists": current_player['assists'],
                "missed_shots": fga_diff - fgm_diff,
            })
    
    return {
        "first_check": False,
        "minutes_since_last": 3,
        "changes": changes,
    }


@mcp.tool()
async def save_snapshot(
    game_id: str,
    period: int,
    game_clock: str,
    heat_score: int,
    opponent_score: int,
    heat_stats: List[Dict]
) -> Dict[str, Any]:
    """Save current snapshot"""
    global LAST_SNAPSHOT
    
    LAST_SNAPSHOT = heat_stats
    
    return {
        "success": True,
        "snapshot_id": GAME_STATE["check_count"],
        "saved_at": str(datetime.utcnow())
    }


@mcp.tool()
async def post_heat_tweet(tweet_text: str, game_id: str, snapshot_id: int) -> Dict[str, Any]:
    """Post tweet (just prints in test mode)"""
    print("\n" + "="*60)
    print("🔥 WOULD POST TWEET:")
    print("="*60)
    print(tweet_text)
    print("="*60 + "\n")
    
    return {
        "success": True,
        "tweet_id": f"test_tweet_{snapshot_id}",
        "tweet_text": tweet_text
    }


@mcp.tool()
async def check_recent_heat_tweets(game_id: str, minutes: int = 5) -> Dict[str, Any]:
    """Check recent tweets (always returns False in test mode to allow tweeting)"""
    return {
        "recently_tweeted": False,
        "message": "TEST MODE - Clear to tweet"
    }


if __name__ == "__main__":
    mcp.run()

