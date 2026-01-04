#!/usr/bin/env python3
"""
MCP Server for NBA Agent - Exposes NBA data and Twitter posting to AI agents.

This allows LangChain or other AI clients to interact with your NBA bot.
"""
import asyncio
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from loguru import logger

from clients import NBAClient, TwitterClient
from analyzers import BoxScoreFormatter, InjuryDetector
from database import DatabaseManager, BoxScorePost, ProcessedTweet
from config import settings

# Initialize MCP Server
mcp = FastMCP("NBA-Agent-Server")

# Initialize clients
nba_client = NBAClient()
twitter_client = TwitterClient()
db_manager = DatabaseManager(settings.DATABASE_URL)
db_manager.create_tables()
formatter = BoxScoreFormatter()

# Initialize injury detector only if tweet monitoring is enabled
injury_detector = None
if settings.ENABLE_TWEET_MONITORING and settings.ANTHROPIC_API_KEY:
    injury_detector = InjuryDetector()


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


@mcp.tool()
async def get_recent_tweets(username: str = "ShamsCharania", max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Get recent tweets from a specific Twitter user.
    
    Args:
        username: Twitter username to fetch from
        max_results: Number of tweets to fetch (default: 10)
    
    Returns:
        List of tweet dictionaries
    """
    tweets = twitter_client.get_user_recent_tweets(username, max_results=max_results)
    return tweets


@mcp.tool()
async def analyze_tweet_for_injury(tweet_text: str) -> Dict[str, Any]:
    """
    Analyze a tweet to determine if it contains injury information.
    
    Args:
        tweet_text: The text of the tweet to analyze
    
    Returns:
        Dictionary with is_injury, confidence, and summary
    """
    if not injury_detector:
        return {
            "error": "Injury detection not enabled. Set ENABLE_TWEET_MONITORING=true and ANTHROPIC_API_KEY in .env"
        }
    
    result = injury_detector.is_injury_related(tweet_text)
    return result


@mcp.tool()
async def generate_injury_summary(original_tweet: str) -> str:
    """
    Generate a concise, original tweet summarizing injury news from a source tweet.
    
    Args:
        original_tweet: The original tweet text with injury info
    
    Returns:
        Generated summary tweet text
    """
    if not injury_detector:
        return "Error: Injury detection not enabled"
    
    from anthropic import Anthropic
    
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    prompt = f"""Create a concise, original tweet (max 280 chars) summarizing this injury news:

Original: "{original_tweet}"

Requirements:
- Be informative and clear
- Include player name, team, injury type
- Include timeline if mentioned (weeks out, questionable, etc.)
- Use 🏥 emoji
- Don't copy the original verbatim - rewrite in your own words
- Keep it under 280 characters

Respond with ONLY the tweet text, nothing else."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        tweet_text = response.content[0].text.strip()
        
        # Remove quotes if present
        if tweet_text.startswith('"') and tweet_text.endswith('"'):
            tweet_text = tweet_text[1:-1]
        
        # Ensure it's under 280 chars
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."
        
        return tweet_text
    except Exception as e:
        logger.error(f"Error generating injury summary: {e}")
        return f"🏥 Injury Update: {original_tweet[:200]}..."


@mcp.tool()
async def post_injury_tweet(player_name: str, injury_type: str, time_missed: Optional[str] = None) -> Dict[str, Any]:
    """
    Post a tweet about a player injury.
    
    Args:
        player_name: Name of the injured player
        injury_type: Type of injury
        time_missed: Expected time missed (optional)
    
    Returns:
        Dictionary with success status and tweet_id
    """
    # Format the injury tweet
    if time_missed:
        tweet_text = f"🏥 Injury Report: {player_name} - {injury_type}. Expected to miss {time_missed}."
    else:
        tweet_text = f"🏥 Injury Report: {player_name} - {injury_type}."
    
    # Post to Twitter
    tweet_id = twitter_client.post_tweet(tweet_text)
    
    if tweet_id:
        return {
            "success": True,
            "tweet_id": tweet_id,
            "tweet_text": tweet_text
        }
    else:
        return {
            "success": False,
            "error": "Failed to post tweet"
        }


@mcp.tool()
async def check_and_post_injury_tweets(username: str = "ShamsCharania") -> Dict[str, Any]:
    """
    Check for new injury-related tweets and post about them.
    Automatically tracks which tweets have been processed.
    
    Args:
        username: Twitter username to monitor
    
    Returns:
        Summary of processed tweets
    """
    if not injury_detector:
        return {
            "error": "Injury detection not enabled. Set ENABLE_TWEET_MONITORING=true and ANTHROPIC_API_KEY in .env"
        }
    
    session = db_manager.get_session()
    
    try:
        # Get last processed tweet ID
        last_tweet = (
            session.query(ProcessedTweet)
            .filter_by(author_username=username)
            .order_by(ProcessedTweet.processed_at.desc())
            .first()
        )
        
        since_id = last_tweet.tweet_id if last_tweet else None
        
        # Fetch new tweets
        tweets = twitter_client.get_user_recent_tweets(
            username=username,
            max_results=5,
            since_id=since_id
        )
        
        if not tweets:
            return {
                "new_tweets": 0,
                "injury_tweets": 0,
                "posted": 0,
                "message": "No new tweets found"
            }
        
        injury_count = 0
        posted_count = 0
        debug_log = []
        
        debug_log.append(f"\n{'='*60}")
        debug_log.append(f"🔍 DEBUGGING: Analyzing {len(tweets)} tweets from @{username}")
        debug_log.append(f"{'='*60}\n")
        
        for i, tweet in enumerate(tweets, 1):
            tweet_id = tweet['id']
            tweet_text = tweet['text']
            
            debug_log.append(f"\n📱 Tweet {i}/{len(tweets)}:")
            debug_log.append(f"   ID: {tweet_id}")
            debug_log.append(f"   Text: {tweet_text[:200]}{'...' if len(tweet_text) > 200 else ''}")
            
            # Check if already processed
            existing = session.query(ProcessedTweet).filter_by(tweet_id=tweet_id).first()
            if existing:
                debug_log.append(f"   ⏭️  Already processed - skipping")
                continue
            
            # Analyze for injury
            debug_log.append(f"   🤖 Analyzing with Claude...")
            analysis = injury_detector.is_injury_related(tweet_text)
            is_injury = analysis.get('is_injury', False)
            confidence = analysis.get('confidence', 0.0)
            summary = analysis.get('summary', 'No summary')
            
            debug_log.append(f"   📊 Result: {'✅ INJURY' if is_injury else '❌ Not injury'} (confidence: {confidence:.2f})")
            debug_log.append(f"   💬 Summary: {summary}")
            
            # Create database record
            processed_tweet = ProcessedTweet(
                tweet_id=tweet_id,
                author_username=username,
                tweet_text=tweet_text,
                is_injury_related=is_injury,
                reposted=False,
                processed_at=datetime.utcnow()
            )
            
            # If injury-related and high confidence, create original tweet
            if is_injury and confidence >= 0.7:
                injury_count += 1
                debug_log.append(f"   🏥 HIGH CONFIDENCE INJURY - Generating summary tweet...")
                
                # Generate original summary tweet using Claude
                from anthropic import Anthropic
                client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                
                try:
                    prompt = f"""Create a concise, original tweet (max 280 chars) summarizing this injury news:

Original: "{tweet_text}"

Requirements:
- Be informative and clear
- Include player name, team, injury type
- Include timeline if mentioned (weeks out, questionable, etc.)
- Use 🏥 emoji
- Don't copy the original verbatim - rewrite in your own words
- Keep it under 280 characters

Respond with ONLY the tweet text, nothing else."""

                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=150,
                        temperature=0.7,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    summary_tweet = response.content[0].text.strip()
                    
                    # Remove quotes if present
                    if summary_tweet.startswith('"') and summary_tweet.endswith('"'):
                        summary_tweet = summary_tweet[1:-1]
                    
                    # Ensure it's under 280 chars
                    if len(summary_tweet) > 280:
                        summary_tweet = summary_tweet[:277] + "..."
                    
                    debug_log.append(f"   📝 Generated: {summary_tweet}")
                    
                    # Post the summary tweet
                    posted_tweet_id = twitter_client.post_tweet(summary_tweet)
                    
                    if posted_tweet_id:
                        processed_tweet.reposted = True
                        processed_tweet.repost_id = posted_tweet_id
                        posted_count += 1
                        debug_log.append(f"   ✅ Successfully posted! Tweet ID: {posted_tweet_id}")
                    else:
                        # Failed to post, but still mark as processed to avoid retrying
                        processed_tweet.reposted = False
                        debug_log.append(f"   ❌ Failed to post (rate limit or error)")
                        
                except Exception as e:
                    logger.error(f"Error generating/posting injury tweet: {e}")
                    debug_log.append(f"   ❌ Error: {str(e)}")
                    # Still mark as processed to avoid infinite retries
                    processed_tweet.reposted = False
                    
            elif is_injury:
                debug_log.append(f"   ⚠️  Injury detected but confidence too low ({confidence:.2f} < 0.7)")
            
            # Always add to session, even if posting failed (to avoid retrying)
            session.add(processed_tweet)
        
        debug_log.append(f"\n{'='*60}")
        debug_log.append(f"📈 SUMMARY: {len(tweets)} tweets analyzed, {injury_count} injuries found, {posted_count} posted")
        debug_log.append(f"{'='*60}\n")
        
        session.commit()
        
        # Join debug log into a string to return
        debug_output = "\n".join(debug_log)
        
        return {
            "new_tweets": len(tweets),
            "injury_tweets": injury_count,
            "posted": posted_count,
            "message": f"Processed {len(tweets)} tweets, found {injury_count} injuries, posted {posted_count}",
            "debug": debug_output
        }
        
    except Exception as e:
        session.rollback()
        return {
            "error": str(e)
        }
    finally:
        session.close()


if __name__ == "__main__":
    # MCP servers run over stdio (Standard Input/Output)
    # This allows an LLM client (like Claude via LangChain) to communicate
    mcp.run()

