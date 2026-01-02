"""
Agent for posting NBA box scores.
"""
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from clients import TwitterClient, NBAClient
from analyzers import BoxScoreFormatter
from database import BoxScorePost, DatabaseManager


class BoxScoreAgent:
    """Agent that posts NBA box scores to Twitter."""
    
    def __init__(
        self,
        twitter_client: TwitterClient,
        nba_client: NBAClient,
        db_manager: DatabaseManager
    ):
        """
        Initialize the box score agent.
        
        Args:
            twitter_client: Twitter API client
            nba_client: NBA API client
            db_manager: Database manager
        """
        self.twitter_client = twitter_client
        self.nba_client = nba_client
        self.db_manager = db_manager
        self.formatter = BoxScoreFormatter()
    
    def post_recent_box_scores(self):
        """
        Check for completed games and post their box scores.
        """
        logger.info("Checking for completed games to post")
        
        session = self.db_manager.get_session()
        
        try:
            # Get completed games from today
            games = self.nba_client.get_completed_games_today()
            
            if not games:
                logger.info("No completed games found")
                return
            
            logger.info(f"Found {len(games)} completed games")
            
            # Process each game
            for game in games:
                self._post_game_box_score(game, session)
            
            session.commit()
            logger.info("Successfully processed all box scores")
            
        except Exception as e:
            logger.error(f"Error posting box scores: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _post_game_box_score(self, game: Dict[str, Any], session: Session):
        """
        Post a single game's box score.
        
        Args:
            game: Game data dictionary
            session: Database session
        """
        game_id = game['game_id']
        
        logger.info(f"Processing game {game_id}")
        
        # Check if already posted
        existing = session.query(BoxScorePost).filter_by(game_id=game_id).first()
        if existing:
            logger.info(f"Game {game_id} already posted, skipping")
            return
        
        try:
            # Get top performers for more engaging tweet
            top_performers = self.nba_client.get_top_performers(game_id, top_n=1)
            
            # Format the tweet
            if top_performers:
                tweet_text = self.formatter.format_game_with_top_performers(
                    game, top_performers
                )
            else:
                tweet_text = self.formatter.format_game_summary(game)
            
            logger.info(f"Posting box score for game {game_id}")
            
            # Post to Twitter
            tweet_id = self.twitter_client.post_tweet(tweet_text)
            
            # Create database record
            box_score_post = BoxScorePost(
                game_id=game_id,
                game_date=datetime.strptime(game['game_date'], "%Y-%m-%d"),
                home_team=game['home_team'],
                away_team=game['away_team'],
                home_score=game.get('home_score', 0),
                away_score=game.get('away_score', 0),
                post_text=tweet_text,
                tweet_id=tweet_id,
                posted_at=datetime.utcnow()
            )
            
            session.add(box_score_post)
            session.flush()
            
            if tweet_id:
                logger.info(f"Successfully posted box score for game {game_id} as tweet {tweet_id}")
            else:
                logger.warning(f"Failed to post box score for game {game_id}")
                
        except Exception as e:
            logger.error(f"Error posting box score for game {game_id}: {e}")
    
    def post_daily_summary(self):
        """
        Post a summary of all games from today.
        """
        logger.info("Creating daily game summary")
        
        try:
            games = self.nba_client.get_completed_games_today()
            
            if not games:
                logger.info("No games to summarize")
                return
            
            tweet_text = self.formatter.format_multiple_games(games)
            
            if tweet_text:
                tweet_id = self.twitter_client.post_tweet(tweet_text)
                
                if tweet_id:
                    logger.info(f"Posted daily summary as tweet {tweet_id}")
                else:
                    logger.warning("Failed to post daily summary")
                    
        except Exception as e:
            logger.error(f"Error posting daily summary: {e}")

