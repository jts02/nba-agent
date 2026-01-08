"""
Twitter API client for fetching and posting tweets.
"""
import tweepy
from typing import List, Optional, Dict, Any
from loguru import logger
from config import settings


class TwitterClient:
    """Client for interacting with Twitter API."""
    
    def __init__(self):
        """Initialize Twitter client with API credentials."""
        self.client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        
    def get_user_recent_tweets(
        self,
        username: str,
        max_results: int = 10,
        since_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent tweets from a specific user.
        
        Args:
            username: Twitter username to fetch tweets from
            max_results: Maximum number of tweets to fetch (5-100)
            since_id: Only return tweets after this tweet ID
            
        Returns:
            List of tweet dictionaries
        """
        try:
            # Get user ID from username
            user = self.client.get_user(username=username)
            if not user.data:
                logger.error(f"User {username} not found")
                return []
            
            user_id = user.data.id
            
            # Fetch tweets
            kwargs = {
                "id": user_id,
                "max_results": min(max_results, 100),
                "tweet_fields": ["id", "text", "created_at", "author_id"],
            }
            
            if since_id:
                kwargs["since_id"] = since_id
            
            tweets = self.client.get_users_tweets(**kwargs)
            
            if not tweets.data:
                logger.info(f"No new tweets from {username}")
                return []
            
            return [
                {
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "created_at": tweet.created_at,
                    "author_id": str(tweet.author_id),
                }
                for tweet in tweets.data
            ]
            
        except tweepy.TweepyException as e:
            logger.error(f"Error fetching tweets from {username}: {e}")
            return []
    
    def retweet(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """
        Retweet a specific tweet.
        
        Args:
            tweet_id: ID of the tweet to retweet
            
        Returns:
            Response data or None if failed
        """
        try:
            response = self.client.retweet(tweet_id)
            logger.info(f"Successfully retweeted tweet {tweet_id}")
            return response
        except tweepy.TweepyException as e:
            logger.error(f"Error retweeting {tweet_id}: {e}")
            return None
    
    def quote_tweet(self, tweet_id: str, comment: str) -> Optional[str]:
        """
        Quote tweet with additional commentary.
        
        Args:
            tweet_id: ID of the tweet to quote
            comment: Additional commentary to add
            
        Returns:
            ID of the new tweet or None if failed
        """
        try:
            # Get the original tweet URL
            original_tweet = self.client.get_tweet(tweet_id)
            if not original_tweet.data:
                logger.error(f"Tweet {tweet_id} not found")
                return None
            
            # Create quoted tweet
            tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
            full_text = f"{comment}\n\n{tweet_url}"
            
            response = self.client.create_tweet(text=full_text)
            
            if response.data:
                tweet_id = str(response.data["id"])
                logger.info(f"Successfully quoted tweet as {tweet_id}")
                return tweet_id
            
            return None
            
        except tweepy.TweepyException as e:
            logger.error(f"Error quoting tweet {tweet_id}: {e}")
            return None
    
    def post_tweet(self, text: str, reply_to_tweet_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Post a new tweet, optionally as a reply to another tweet.
        
        Args:
            text: Tweet text (max 280 characters)
            reply_to_tweet_id: Optional tweet ID to reply to
            
        Returns:
            Dict with tweet data or None if failed
        """
        try:
            if len(text) > 280:
                logger.warning(f"Tweet text too long ({len(text)} chars), truncating")
                text = text[:277] + "..."
            
            kwargs = {"text": text}
            if reply_to_tweet_id:
                kwargs["in_reply_to_tweet_id"] = reply_to_tweet_id
            
            response = self.client.create_tweet(**kwargs)
            
            if response.data:
                tweet_id = str(response.data["id"])
                if reply_to_tweet_id:
                    logger.info(f"Successfully posted reply {tweet_id} to tweet {reply_to_tweet_id}")
                else:
                    logger.info(f"Successfully posted tweet {tweet_id}")
                return response.data
            
            return None
            
        except tweepy.TweepyException as e:
            logger.error(f"Error posting tweet: {e}")
            return None
    
    def reply_to_tweet(self, tweet_id: str, reply_text: str) -> Optional[Dict[str, Any]]:
        """
        Reply directly to a specific tweet.
        
        Args:
            tweet_id: ID of the tweet to reply to
            reply_text: Text of the reply (max 280 characters)
            
        Returns:
            Dict with reply tweet data or None if failed
        """
        return self.post_tweet(reply_text, reply_to_tweet_id=tweet_id)
    
    def get_latest_tweet_id(self, username: str) -> Optional[str]:
        """
        Get the ID of the most recent tweet from a user.
        
        Args:
            username: Twitter username
            
        Returns:
            Tweet ID or None if not found
        """
        tweets = self.get_user_recent_tweets(username, max_results=5)
        if tweets:
            return tweets[0]["id"]
        return None

