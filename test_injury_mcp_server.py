#!/usr/bin/env python3
"""
Test MCP Server for Injury Monitoring - Uses dummy tweet data.

Run with: python ai_agent.py test --injury
"""
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from clients import TwitterClient
from database import DatabaseManager, ProcessedTweet
from config import settings

# Initialize MCP Server
mcp = FastMCP("NBA-Agent-Injury-Test-Server")

# Initialize clients
twitter_client = TwitterClient()
db_manager = DatabaseManager(settings.DATABASE_URL)
db_manager.create_tables()

# Load test data
with open("test_injury_data.json", "r") as f:
    test_data = json.load(f)


@mcp.tool()
async def get_recent_tweets(username: str = "ShamsCharania", max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent tweets from test data (simulates Twitter API).
    
    Args:
        username: Twitter username (ignored in test mode)
        max_results: Number of tweets to return
    
    Returns:
        List of tweet dictionaries
    """
    tweets = test_data["tweets"][:max_results]
    return tweets


@mcp.tool()
async def analyze_tweet_for_injury(tweet_text: str) -> Dict[str, Any]:
    """
    Analyze a tweet to determine if it contains injury information.
    In test mode, uses simple keyword matching instead of OpenAI.
    
    Args:
        tweet_text: The text of the tweet to analyze
    
    Returns:
        Dictionary with is_injury, confidence, and summary
    """
    # Simple keyword-based detection for testing
    injury_keywords = [
        "injury", "injured", "hurt", "sprain", "strain", "tear", "torn",
        "surgery", "MRI", "out", "miss", "questionable", "doubtful", "ruled out"
    ]
    
    text_lower = tweet_text.lower()
    keyword_count = sum(1 for keyword in injury_keywords if keyword in text_lower)
    
    is_injury = keyword_count >= 2
    confidence = min(0.9, 0.5 + (keyword_count * 0.15))
    
    # Extract player name (simple heuristic)
    words = tweet_text.split()
    player_name = "Unknown Player"
    for i, word in enumerate(words):
        if word in ["Lakers", "Warriors", "Celtics", "Heat", "Suns", "Bucks", "76ers", "Knicks"]:
            if i > 0:
                player_name = " ".join(words[max(0, i-2):i])
                break
    
    return {
        "is_injury": is_injury,
        "confidence": confidence,
        "summary": f"Detected injury-related content (confidence: {confidence:.2f})",
        "player_name": player_name.strip("':")
    }


@mcp.tool()
async def extract_injury_details(tweet_text: str) -> Dict[str, Any]:
    """
    Extract specific injury details from a tweet.
    
    Args:
        tweet_text: The tweet text
    
    Returns:
        Dictionary with player_name, injury_type, and time_missed
    """
    # Simple extraction for testing
    player_name = "Unknown Player"
    injury_type = "injury"
    time_missed = None
    
    # Extract player name (look for patterns like "Player Name will" or "Player Name (")
    import re
    
    # Pattern 1: "Name will miss/undergo"
    match = re.search(r"([A-Z][a-z]+ [A-Z][a-z]+(?:'s)?)\s+(?:will|has|underwent|suffered)", tweet_text)
    if match:
        player_name = match.group(1).replace("'s", "")
    
    # Pattern 2: "Team's Player Name"
    if player_name == "Unknown Player":
        match = re.search(r"(?:Lakers|Warriors|Celtics|Heat|Suns|Bucks|76ers|Knicks)(?:'s)?\s+([A-Z][a-z]+ [A-Z][a-z]+)", tweet_text)
        if match:
            player_name = match.group(1)
    
    # Extract injury type
    injury_keywords = {
        "ankle": "ankle injury",
        "knee": "knee injury",
        "shoulder": "shoulder injury",
        "thumb": "thumb injury",
        "sprain": "sprain",
        "strain": "strain",
        "torn": "torn ligament",
        "surgery": "surgery"
    }
    
    for keyword, injury_name in injury_keywords.items():
        if keyword in tweet_text.lower():
            injury_type = injury_name
            break
    
    # Extract time missed
    time_patterns = [
        r"(\d+-\d+\s+(?:weeks|days|months))",
        r"(\d+\s+(?:weeks|days|months))",
        r"miss\s+(\d+\s+games?)",
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, tweet_text, re.IGNORECASE)
        if match:
            time_missed = match.group(1)
            break
    
    return {
        "player_name": player_name,
        "injury_type": injury_type,
        "time_missed": time_missed
    }


@mcp.tool()
async def post_injury_tweet(player_name: str, injury_type: str, time_missed: Optional[str] = None) -> Dict[str, Any]:
    """
    Post a tweet about a player injury. In TEST MODE, only prints the tweet.
    
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
    """
    Check for new injury-related tweets and post about them.
    In TEST MODE, uses dummy data and doesn't actually post.
    
    Args:
        username: Twitter username to monitor
    
    Returns:
        Summary of processed tweets
    """
    session = db_manager.get_session()
    
    try:
        # Get test tweets
        tweets = test_data["tweets"]
        
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
                
                # Extract details and post
                details = await extract_injury_details(tweet_text)
                result = await post_injury_tweet(
                    details['player_name'],
                    details['injury_type'],
                    details.get('time_missed')
                )
                
                if result.get('success'):
                    processed_tweet.reposted = True
                    processed_tweet.repost_id = result['tweet_id']
                    posted_count += 1
                    
                    processed_tweets.append({
                        "tweet_id": tweet_id,
                        "player": details['player_name'],
                        "injury": details['injury_type'],
                        "time_missed": details.get('time_missed'),
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
            "note": "TEST MODE - No actual tweets were posted to Twitter"
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
    """
    Get all processed injury tweets from database.
    """
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

