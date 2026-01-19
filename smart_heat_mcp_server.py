#!/usr/bin/env python3
"""
Smart Heat Bot MCP Server - Memory, Context, and Intelligent Tweet Generation

This MCP server provides tools for:
- Monitoring Heat Twitter accounts and building memory
- Tracking narratives and storylines
- Storing Heat knowledge base
- Live game monitoring
- Context-aware tweet generation
- Performance tracking
"""
import asyncio
import json
import os
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from loguru import logger
from sqlalchemy import desc, and_

from clients import NBAClient, TwitterClient
from database import (
    DatabaseManager,
    MonitoredTweet,
    HeatNarrative,
    HeatKnowledge,
    SmartBotTweet
)
from config import settings

# Initialize MCP Server
mcp = FastMCP("Smart-Heat-Bot-Server")

# Initialize clients
nba_client = NBAClient()
twitter_client = TwitterClient()
db_manager = DatabaseManager(settings.DATABASE_URL)
db_manager.create_tables()

# Heat Twitter accounts to monitor (NO player accounts - they change teams)
HEAT_ACCOUNTS = {
    "beat_reporters": ["IraHeatBeat", "Anthony_Chiang", "AhnFireDigital"],
    "influencers": ["5ReasonsSports", "HeatVsHaters", "MiamiHeatBeat", "ChefTrillie", "BradyHawk305"],
    "official": ["MiamiHEAT"],  # Just official team account
    "nba_news": ["ShamsCharania"]
}


# ============================================================
# TWITTER MONITORING TOOLS
# ============================================================

@mcp.tool()
async def scrape_heat_twitter(
    account_category: str = "all",
    max_tweets_per_account: int = 5,
    hours_back: int = 24
) -> Dict[str, Any]:
    """
    Scrape recent tweets from Heat Twitter accounts and store them for learning.
    HANDLES RATE LIMITS: If rate limited, returns partial results and tells you to wait.

    IMPORTANT: Twitter Free Tier only allows ~50 tweets per day!
    - Use max_tweets_per_account=5 or lower
    - Scrape specific categories instead of "all"
    - Use longer intervals (60+ minutes)

    Args:
        account_category: Which accounts to scrape - "beat_reporters", "influencers",
                         "official", "nba_news", or "all"
        max_tweets_per_account: Max tweets to fetch per account (default: 5 to avoid rate limits!)
        hours_back: Only get tweets from last N hours

    Returns:
        Summary of tweets scraped and stored (may be partial if rate limited)
    """
    session = db_manager.get_session()

    try:
        # Determine which accounts to scrape
        if account_category == "all":
            accounts_to_scrape = []
            for category, usernames in HEAT_ACCOUNTS.items():
                accounts_to_scrape.extend(usernames)
        elif account_category in HEAT_ACCOUNTS:
            accounts_to_scrape = HEAT_ACCOUNTS[account_category]
        else:
            return {"error": f"Invalid category: {account_category}"}

        total_scraped = 0
        total_new = 0
        accounts_attempted = 0
        accounts_succeeded = 0
        rate_limited = False
        rate_limit_wait_minutes = 0
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        for username in accounts_to_scrape:
            accounts_attempted += 1
            logger.info(f"Scraping @{username}...")

            try:
                # Get last tweet ID we scraped for this account (for efficiency)
                last_tweet = session.query(MonitoredTweet).filter_by(
                    author_username=username
                ).order_by(MonitoredTweet.scraped_at.desc()).first()

                since_id = last_tweet.tweet_id if last_tweet else None

                if since_id:
                    logger.info(f"  Fetching tweets since ID {since_id} (only new tweets)")
                else:
                    logger.info(f"  First time scraping @{username}, fetching recent {max_tweets_per_account} tweets")

                # Get recent tweets - only NEW ones since last check!
                tweets = twitter_client.get_user_recent_tweets(
                    username=username,
                    max_results=max_tweets_per_account,
                    since_id=since_id  # Only tweets after this ID
                )

                if not tweets:
                    logger.info(f"  No new tweets from @{username}")
                    continue

                logger.info(f"  Found {len(tweets)} new tweet(s) from @{username}")
                accounts_succeeded += 1

                for tweet in tweets:
                    try:
                        tweet_id = tweet.get('id')
                        tweet_text = tweet.get('text', '')

                        # Check if already monitored
                        existing = session.query(MonitoredTweet).filter_by(
                            tweet_id=tweet_id
                        ).first()

                        if existing:
                            # Update engagement metrics
                            existing.likes = tweet.get('public_metrics', {}).get('like_count', 0)
                            existing.retweets = tweet.get('public_metrics', {}).get('retweet_count', 0)
                            existing.replies = tweet.get('public_metrics', {}).get('reply_count', 0)
                        else:
                            # Parse timestamp safely
                            tweet_created_at = None
                            if tweet.get('created_at'):
                                try:
                                    created_at_str = tweet.get('created_at')
                                    # Handle different timestamp formats
                                    if isinstance(created_at_str, str):
                                        created_at_str = created_at_str.replace('Z', '+00:00')
                                        tweet_created_at = datetime.fromisoformat(created_at_str)
                                except Exception as ts_error:
                                    logger.warning(f"Could not parse timestamp '{tweet.get('created_at')}': {ts_error}")

                            # Create new monitored tweet
                            new_tweet = MonitoredTweet(
                                tweet_id=tweet_id,
                                author_username=username,
                                author_display_name=tweet.get('author', {}).get('name'),
                                tweet_text=tweet_text,
                                tweet_type="original",  # TODO: detect reply/quote/rt
                                likes=tweet.get('public_metrics', {}).get('like_count', 0),
                                retweets=tweet.get('public_metrics', {}).get('retweet_count', 0),
                                replies=tweet.get('public_metrics', {}).get('reply_count', 0),
                                tweet_created_at=tweet_created_at
                            )
                            session.add(new_tweet)
                            total_new += 1

                        total_scraped += 1

                    except Exception as tweet_error:
                        logger.error(f"Error processing tweet from @{username}: {tweet_error}")
                        continue

                # Add delay between accounts to avoid rate limits (2 seconds)
                if accounts_attempted < len(accounts_to_scrape):
                    logger.info(f"Waiting 2 seconds before next account...")
                    time.sleep(2)

            except Exception as account_error:
                error_str = str(account_error).lower()

                # Check if it's a rate limit error
                if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
                    logger.warning(f"⚠️ RATE LIMITED while scraping @{username}")
                    logger.warning(f"   Twitter Free Tier limit reached!")
                    logger.warning(f"   You're on Free Tier: ~50 tweets/day limit")

                    rate_limited = True

                    # Check if it's the severe free tier limit (900 second wait)
                    if "900" in error_str or "15 minute" in error_str:
                        rate_limit_wait_minutes = 900 // 60  # 15 minutes
                        logger.warning(f"   Severe rate limit: Wait 15 minutes before next request")
                    else:
                        rate_limit_wait_minutes = 15
                        logger.warning(f"   Standard rate limit: Wait {rate_limit_wait_minutes} minutes")

                    # Stop trying more accounts - we're rate limited
                    break
                else:
                    # Some other error for this account, log and continue
                    logger.error(f"❌ Error scraping @{username}: {account_error}")
                    import traceback
                    logger.error(f"   Traceback: {traceback.format_exc()[:500]}")
                    continue

        # Commit what we got before the rate limit
        session.commit()

        result = {
            "success": not rate_limited,  # Only fully successful if no rate limit
            "accounts_attempted": accounts_attempted,
            "accounts_succeeded": accounts_succeeded,
            "total_tweets": total_scraped,
            "new_tweets": total_new,
            "updated_tweets": total_scraped - total_new
        }

        if rate_limited:
            result["rate_limited"] = True
            result["wait_minutes"] = rate_limit_wait_minutes
            result["message"] = f"⚠️ RATE LIMITED after {accounts_succeeded}/{accounts_attempted} accounts. Wait {rate_limit_wait_minutes} minutes before scraping again."
            result["suggestion"] = "Consider: 1) Reduce max_tweets_per_account, 2) Scrape specific categories instead of 'all', 3) Increase time between scrapes"
        else:
            result["message"] = f"✅ Successfully scraped {accounts_succeeded} accounts"

        return result

    except Exception as e:
        session.rollback()
        error_str = str(e).lower()

        if "rate limit" in error_str or "429" in error_str:
            logger.error(f"Rate limited: {e}")
            return {
                "error": "Rate limited by Twitter API",
                "rate_limited": True,
                "wait_minutes": 15,
                "message": "⚠️ Twitter API rate limit hit. Wait 15 minutes before trying again.",
                "partial_results": {
                    "tweets_saved_before_limit": total_scraped,
                    "accounts_completed": accounts_succeeded
                }
            }
        else:
            logger.error(f"Error scraping Heat Twitter: {e}")
            return {"error": str(e)}
    finally:
        session.close()


@mcp.tool()
async def get_heat_twitter_context(hours_back: int = 6, limit: int = 30) -> Dict[str, Any]:
    """
    Get recent Heat Twitter context to understand what's being discussed.
    Returns recent tweets, top topics, and sentiment.

    Args:
        hours_back: How many hours back to look
        limit: Max tweets to return

    Returns:
        Recent tweets and analysis
    """
    session = db_manager.get_session()

    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        # Get recent monitored tweets
        recent_tweets = session.query(MonitoredTweet).filter(
            MonitoredTweet.scraped_at >= cutoff_time
        ).order_by(
            desc(MonitoredTweet.scraped_at)
        ).limit(limit).all()

        # Format for context
        tweets_data = []
        for tweet in recent_tweets:
            tweets_data.append({
                "author": tweet.author_username,
                "text": tweet.tweet_text,
                "engagement": {
                    "likes": tweet.likes,
                    "retweets": tweet.retweets,
                    "replies": tweet.replies
                },
                "created_at": tweet.tweet_created_at.isoformat() if tweet.tweet_created_at else None
            })

        # Get top engaged tweets
        top_engaged = sorted(
            tweets_data,
            key=lambda x: x['engagement']['likes'] + x['engagement']['retweets'] * 2,
            reverse=True
        )[:5]

        return {
            "recent_tweets": tweets_data,
            "top_engaged_tweets": top_engaged,
            "total_found": len(tweets_data),
            "time_range_hours": hours_back
        }

    except Exception as e:
        logger.error(f"Error getting Heat Twitter context: {e}")
        return {"error": str(e)}
    finally:
        session.close()


# ============================================================
# NARRATIVE TRACKING TOOLS
# ============================================================

@mcp.tool()
async def get_active_narratives() -> Dict[str, Any]:
    """
    Get currently active Heat narratives and storylines.
    These are ongoing stories that the bot should be aware of.

    Returns:
        List of active narratives with details
    """
    session = db_manager.get_session()

    try:
        active_narratives = session.query(HeatNarrative).filter(
            HeatNarrative.status == "active"
        ).order_by(
            desc(HeatNarrative.last_updated)
        ).all()

        narratives_data = []
        for narrative in active_narratives:
            narratives_data.append({
                "key": narrative.narrative_key,
                "title": narrative.title,
                "description": narrative.description,
                "players": json.loads(narrative.player_names) if narrative.player_names else [],
                "topics": json.loads(narrative.related_topics) if narrative.related_topics else [],
                "started": narrative.started_at.isoformat(),
                "last_updated": narrative.last_updated.isoformat()
            })

        return {
            "active_narratives": narratives_data,
            "count": len(narratives_data)
        }

    except Exception as e:
        logger.error(f"Error getting active narratives: {e}")
        return {"error": str(e)}
    finally:
        session.close()


@mcp.tool()
async def update_narrative(
    narrative_key: str,
    title: str,
    description: str,
    status: str = "active",
    players: List[str] = None,
    topics: List[str] = None
) -> Dict[str, Any]:
    """
    Create or update a Heat narrative/storyline.

    Args:
        narrative_key: Unique key (e.g., "bam_struggles_jan_2026")
        title: Short title (e.g., "Bam's Shooting Slump")
        description: Detailed description
        status: "active", "resolved", or "dormant"
        players: List of player names involved
        topics: List of related topics

    Returns:
        Confirmation of update
    """
    session = db_manager.get_session()

    try:
        existing = session.query(HeatNarrative).filter_by(
            narrative_key=narrative_key
        ).first()

        if existing:
            # Update existing
            existing.title = title
            existing.description = description
            existing.status = status
            existing.player_names = json.dumps(players) if players else None
            existing.related_topics = json.dumps(topics) if topics else None
            existing.last_updated = datetime.utcnow()
            if status == "resolved":
                existing.ended_at = datetime.utcnow()

            action = "updated"
        else:
            # Create new
            new_narrative = HeatNarrative(
                narrative_key=narrative_key,
                title=title,
                description=description,
                status=status,
                player_names=json.dumps(players) if players else None,
                related_topics=json.dumps(topics) if topics else None
            )
            session.add(new_narrative)
            action = "created"

        session.commit()

        return {
            "success": True,
            "action": action,
            "narrative_key": narrative_key
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Error updating narrative: {e}")
        return {"error": str(e)}
    finally:
        session.close()


# ============================================================
# KNOWLEDGE BASE TOOLS
# ============================================================

@mcp.tool()
async def add_heat_knowledge(
    knowledge_key: str,
    category: str,
    subject: str,
    fact: str,
    source_type: str = "manual",
    confidence: int = 100
) -> Dict[str, Any]:
    """
    Add a fact to the Heat knowledge base.

    Args:
        knowledge_key: Unique key (e.g., "bam_contract_2023")
        category: Category - "player_stat", "team_history", "inside_joke",
                 "heat_culture", "rival_info", etc.
        subject: Subject of fact (player name, event, etc.)
        fact: The actual fact/knowledge
        source_type: Where it came from - "tweet", "game_stat", "article", "manual"
        confidence: Confidence level 0-100

    Returns:
        Confirmation
    """
    session = db_manager.get_session()

    try:
        existing = session.query(HeatKnowledge).filter_by(
            knowledge_key=knowledge_key
        ).first()

        if existing:
            existing.fact = fact
            existing.confidence = confidence
            existing.last_verified = datetime.utcnow()
            action = "updated"
        else:
            new_knowledge = HeatKnowledge(
                knowledge_key=knowledge_key,
                category=category,
                subject=subject,
                fact=fact,
                source_type=source_type,
                confidence=confidence
            )
            session.add(new_knowledge)
            action = "added"

        session.commit()

        return {
            "success": True,
            "action": action,
            "knowledge_key": knowledge_key
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Error adding knowledge: {e}")
        return {"error": str(e)}
    finally:
        session.close()


@mcp.tool()
async def query_heat_knowledge(
    category: str = None,
    subject: str = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Query the Heat knowledge base.

    Args:
        category: Filter by category (optional)
        subject: Filter by subject (optional)
        limit: Max results

    Returns:
        Matching knowledge entries
    """
    session = db_manager.get_session()

    try:
        query = session.query(HeatKnowledge)

        if category:
            query = query.filter(HeatKnowledge.category == category)
        if subject:
            query = query.filter(HeatKnowledge.subject.ilike(f"%{subject}%"))

        results = query.order_by(
            desc(HeatKnowledge.confidence),
            desc(HeatKnowledge.created_at)
        ).limit(limit).all()

        knowledge_data = []
        for item in results:
            knowledge_data.append({
                "key": item.knowledge_key,
                "category": item.category,
                "subject": item.subject,
                "fact": item.fact,
                "confidence": item.confidence,
                "source": item.source_type
            })

        return {
            "knowledge": knowledge_data,
            "count": len(knowledge_data)
        }

    except Exception as e:
        logger.error(f"Error querying knowledge: {e}")
        return {"error": str(e)}
    finally:
        session.close()


# ============================================================
# LIVE GAME TOOLS
# ============================================================

@mcp.tool()
async def get_live_heat_game() -> Dict[str, Any]:
    """
    Check if the Heat have a live game right now.

    Returns:
        Game info if live, or None
    """
    try:
        # Get today's games
        games = nba_client.get_completed_games_today()

        # Check for Heat games
        for game in games:
            if "MIA" in [game.get('home_team'), game.get('away_team')]:
                # Check if game is live (not final)
                if game.get('status') != 'Final':
                    return {
                        "is_live": True,
                        "game_id": game.get('game_id'),
                        "home_team": game.get('home_team'),
                        "away_team": game.get('away_team'),
                        "home_score": game.get('home_score'),
                        "away_score": game.get('away_score'),
                        "status": game.get('status')
                    }

        return {
            "is_live": False,
            "message": "No live Heat game right now"
        }

    except Exception as e:
        logger.error(f"Error checking live Heat game: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_heat_box_score(game_id: str) -> Dict[str, Any]:
    """
    Get detailed box score for a Heat game.

    Args:
        game_id: NBA game ID

    Returns:
        Heat players' stats
    """
    try:
        box_score = nba_client.get_box_score(game_id)

        if not box_score:
            return {"error": f"No box score found for game {game_id}"}

        # Extract Heat players
        heat_players = []
        for team_key in ['home_team', 'away_team']:
            team_name = box_score.get(team_key)
            if team_name == "Miami Heat":
                heat_players = box_score.get(f'{team_key}_players', [])
                break

        return {
            "game_id": game_id,
            "heat_players": heat_players,
            "game_info": {
                "home_team": box_score.get('home_team'),
                "away_team": box_score.get('away_team'),
                "home_score": box_score.get('home_score'),
                "away_score": box_score.get('away_score')
            }
        }

    except Exception as e:
        logger.error(f"Error getting Heat box score: {e}")
        return {"error": str(e)}


# ============================================================
# DISCOURSE TOOLS - Efficient Reply Generation
# ============================================================

@mcp.tool()
async def get_random_heat_tweet_to_reply_to(max_tweets_per_account: int = 5) -> Dict[str, Any]:
    """
    Get a random recent tweet from Heat Twitter to reply to.
    This is MORE EFFICIENT than scraping all accounts - it only scrapes ONE random account.

    Perfect for discourse mode to avoid rate limits!

    Args:
        max_tweets_per_account: Max tweets to fetch (default: 5)

    Returns:
        A random tweet with context about the author and tweet
    """
    import random

    session = db_manager.get_session()

    try:
        # Flatten all accounts into one list
        all_accounts = []
        for category, usernames in HEAT_ACCOUNTS.items():
            for username in usernames:
                all_accounts.append({"username": username, "category": category})

        # Pick a random account
        chosen_account = random.choice(all_accounts)
        username = chosen_account["username"]
        category = chosen_account["category"]

        logger.info(f"Randomly selected @{username} from {category} for discourse")

        # Get recent tweets from just this ONE account
        try:
            tweets = twitter_client.get_user_recent_tweets(
                username=username,
                max_results=max_tweets_per_account
            )

            if not tweets:
                return {
                    "error": f"No recent tweets found from @{username}",
                    "suggestion": "Try running again to pick a different account"
                }

            # Pick a random tweet from this account
            chosen_tweet = random.choice(tweets)

            tweet_id = chosen_tweet.get('id')
            tweet_text = chosen_tweet.get('text', '')

            # Store it in the database for context
            existing = session.query(MonitoredTweet).filter_by(
                tweet_id=tweet_id
            ).first()

            if not existing:
                # Parse timestamp
                tweet_created_at = None
                if chosen_tweet.get('created_at'):
                    try:
                        created_at_str = chosen_tweet.get('created_at').replace('Z', '+00:00')
                        tweet_created_at = datetime.fromisoformat(created_at_str)
                    except Exception:
                        pass

                new_tweet = MonitoredTweet(
                    tweet_id=tweet_id,
                    author_username=username,
                    author_display_name=chosen_tweet.get('author', {}).get('name'),
                    tweet_text=tweet_text,
                    tweet_type="original",
                    likes=chosen_tweet.get('public_metrics', {}).get('like_count', 0),
                    retweets=chosen_tweet.get('public_metrics', {}).get('retweet_count', 0),
                    replies=chosen_tweet.get('public_metrics', {}).get('reply_count', 0),
                    tweet_created_at=tweet_created_at
                )
                session.add(new_tweet)
                session.commit()

            return {
                "success": True,
                "tweet_id": tweet_id,
                "author_username": username,
                "author_category": category,
                "tweet_text": tweet_text,
                "engagement": {
                    "likes": chosen_tweet.get('public_metrics', {}).get('like_count', 0),
                    "retweets": chosen_tweet.get('public_metrics', {}).get('retweet_count', 0),
                    "replies": chosen_tweet.get('public_metrics', {}).get('reply_count', 0)
                },
                "total_tweets_available": len(tweets),
                "message": f"Found tweet from @{username} ({category}) to reply to"
            }

        except Exception as twitter_error:
            error_str = str(twitter_error).lower()

            if "rate limit" in error_str or "429" in error_str:
                return {
                    "error": "Rate limited by Twitter API",
                    "rate_limited": True,
                    "wait_minutes": 15,
                    "message": "⚠️ Twitter API rate limit hit. Wait 15 minutes before trying again."
                }
            else:
                return {
                    "error": f"Failed to get tweets from @{username}: {str(twitter_error)}",
                    "suggestion": "Try running again to pick a different account"
                }

    except Exception as e:
        session.rollback()
        logger.error(f"Error getting random Heat tweet: {e}")
        return {"error": str(e)}
    finally:
        session.close()


# ============================================================
# TWEET GENERATION AND POSTING TOOLS
# ============================================================

@mcp.tool()
async def generate_smart_tweet(
    tweet_type: str,
    context: Dict[str, Any] = None,
    game_id: str = None
) -> str:
    """
    Generate a context-aware Heat tweet. This is just generation -
    use post_smart_tweet() to actually post it.

    Args:
        tweet_type: Type - "game_reaction", "discourse_reply", "original_take", "nostalgia"
        context: Additional context (narratives, recent tweets, knowledge)
        game_id: Related game ID (if applicable)

    Returns:
        Generated tweet text (you should review before posting)
    """
    # This tool returns a summary for Claude to generate the actual tweet
    # Claude has the personality and will craft the tweet based on context

    return json.dumps({
        "instruction": "Generate tweet based on context provided",
        "tweet_type": tweet_type,
        "context_provided": context,
        "game_id": game_id,
        "note": "Claude should craft the actual tweet text with personality"
    })


@mcp.tool()
async def post_smart_tweet(
    tweet_text: str,
    tweet_type: str,
    context_used: Dict[str, Any] = None,
    game_id: str = None,
    reply_to_tweet_id: str = None
) -> Dict[str, Any]:
    """
    Post a tweet and track it in the smart bot system.

    Args:
        tweet_text: The tweet content (max 280 chars)
        tweet_type: Type - "game_reaction", "discourse_reply", "original_take", "nostalgia"
        context_used: What context/narratives were used
        game_id: Related game ID (if applicable)
        reply_to_tweet_id: If replying to another tweet

    Returns:
        Tweet ID and confirmation
    """
    session = db_manager.get_session()

    try:
        # Post to Twitter
        if reply_to_tweet_id:
            result = twitter_client.reply_to_tweet(
                tweet_id=reply_to_tweet_id,
                reply_text=tweet_text
            )
        else:
            result = twitter_client.post_tweet(tweet_text)

        if not result or not result.get('id'):
            return {"error": "Failed to post tweet to Twitter"}

        tweet_id = result['id']

        # Track in database
        bot_tweet = SmartBotTweet(
            tweet_id=tweet_id,
            tweet_text=tweet_text,
            tweet_type=tweet_type,
            context_used=json.dumps(context_used) if context_used else None,
            related_game_id=game_id,
            reply_to_tweet_id=reply_to_tweet_id
        )
        session.add(bot_tweet)
        session.commit()

        return {
            "success": True,
            "tweet_id": tweet_id,
            "tweet_url": f"https://twitter.com/user/status/{tweet_id}",
            "tweet_text": tweet_text
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Error posting smart tweet: {e}")
        return {"error": str(e)}
    finally:
        session.close()


@mcp.tool()
async def get_bot_recent_tweets(hours_back: int = 24, limit: int = 10) -> Dict[str, Any]:
    """
    Get the bot's recent tweets to avoid repetition and check rate limits.

    Args:
        hours_back: How far back to look
        limit: Max tweets to return

    Returns:
        Recent bot tweets
    """
    session = db_manager.get_session()

    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        recent_tweets = session.query(SmartBotTweet).filter(
            SmartBotTweet.posted_at >= cutoff_time
        ).order_by(
            desc(SmartBotTweet.posted_at)
        ).limit(limit).all()

        tweets_data = []
        for tweet in recent_tweets:
            tweets_data.append({
                "tweet_id": tweet.tweet_id,
                "text": tweet.tweet_text,
                "type": tweet.tweet_type,
                "posted_at": tweet.posted_at.isoformat(),
                "engagement": {
                    "likes": tweet.likes,
                    "retweets": tweet.retweets,
                    "replies": tweet.replies
                }
            })

        return {
            "recent_tweets": tweets_data,
            "count": len(tweets_data),
            "hours_back": hours_back
        }

    except Exception as e:
        logger.error(f"Error getting bot recent tweets: {e}")
        return {"error": str(e)}
    finally:
        session.close()


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
