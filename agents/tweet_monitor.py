"""
Agent for monitoring and processing tweets.
"""
from typing import Optional
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from clients import TwitterClient
from analyzers import InjuryDetector
from database import ProcessedTweet, DatabaseManager


class TweetMonitorAgent:
    """Agent that monitors tweets and reposts injury-related ones."""
    
    def __init__(
        self,
        twitter_client: TwitterClient,
        injury_detector: InjuryDetector,
        db_manager: DatabaseManager,
        target_username: str
    ):
        """
        Initialize the tweet monitor agent.
        
        Args:
            twitter_client: Twitter API client
            injury_detector: Injury detection analyzer
            db_manager: Database manager
            target_username: Twitter username to monitor
        """
        self.twitter_client = twitter_client
        self.injury_detector = injury_detector
        self.db_manager = db_manager
        self.target_username = target_username
        
    def get_last_processed_tweet_id(self, session: Session) -> Optional[str]:
        """
        Get the ID of the last processed tweet.
        
        Args:
            session: Database session
            
        Returns:
            Tweet ID or None
        """
        last_tweet = (
            session.query(ProcessedTweet)
            .filter_by(author_username=self.target_username)
            .order_by(ProcessedTweet.processed_at.desc())
            .first()
        )
        
        if last_tweet:
            return last_tweet.tweet_id
        
        return None
    
    def process_new_tweets(self):
        """
        Check for and process new tweets from the target user.
        """
        logger.info(f"Checking for new tweets from @{self.target_username}")
        
        session = self.db_manager.get_session()
        
        try:
            # Get the last processed tweet ID
            since_id = self.get_last_processed_tweet_id(session)
            
            # Fetch new tweets
            tweets = self.twitter_client.get_user_recent_tweets(
                username=self.target_username,
                max_results=10,
                since_id=since_id
            )
            
            if not tweets:
                logger.info("No new tweets found")
                return
            
            logger.info(f"Found {len(tweets)} new tweets")
            
            # Process each tweet
            for tweet in tweets:
                self._process_single_tweet(tweet, session)
            
            session.commit()
            logger.info("Successfully processed all new tweets")
            
        except Exception as e:
            logger.error(f"Error processing tweets: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _process_single_tweet(self, tweet: dict, session: Session):
        """
        Process a single tweet.
        
        Args:
            tweet: Tweet data dictionary
            session: Database session
        """
        tweet_id = tweet['id']
        tweet_text = tweet['text']
        
        logger.info(f"Processing tweet {tweet_id}")
        
        # Check if already processed
        existing = session.query(ProcessedTweet).filter_by(tweet_id=tweet_id).first()
        if existing:
            logger.info(f"Tweet {tweet_id} already processed, skipping")
            return
        
        # Analyze for injury content
        analysis = self.injury_detector.is_injury_related(tweet_text)
        is_injury = analysis.get('is_injury', False)
        confidence = analysis.get('confidence', 0.0)
        
        logger.info(
            f"Tweet {tweet_id} injury analysis: {is_injury} "
            f"(confidence: {confidence})"
        )
        
        # Create database record
        processed_tweet = ProcessedTweet(
            tweet_id=tweet_id,
            author_username=self.target_username,
            tweet_text=tweet_text,
            is_injury_related=is_injury,
            reposted=False,
            processed_at=datetime.utcnow()
        )
        
        # If injury-related and high confidence, repost it
        if is_injury and confidence >= 0.7:
            logger.info(f"Reposting injury tweet {tweet_id}")
            
            # Try to retweet
            retweet_response = self.twitter_client.retweet(tweet_id)
            
            if retweet_response:
                processed_tweet.reposted = True
                logger.info(f"Successfully reposted tweet {tweet_id}")
            else:
                logger.warning(f"Failed to repost tweet {tweet_id}")
        
        session.add(processed_tweet)
        session.flush()

