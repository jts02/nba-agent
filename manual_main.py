#!/usr/bin/env python3
"""
NBA Agent - Main application entry point.

This agent monitors NBA news tweets and posts box scores automatically.
"""
import sys
import time
import signal
from loguru import logger

from config import settings
from utils import setup_logging
from database import DatabaseManager
from clients import TwitterClient, NBAClient
from analyzers import InjuryDetector
from agents import TweetMonitorAgent, BoxScoreAgent
from scheduler import JobScheduler


class NBAAgent:
    """Main NBA Agent application."""
    
    def __init__(self):
        """Initialize the NBA Agent."""
        self.running = False
        self.scheduler = None
        
    def setup(self):
        """Set up all components."""
        logger.info("=" * 60)
        logger.info("NBA Agent Starting Up")
        logger.info("=" * 60)
        
        # Validate configuration
        logger.info("Validating configuration...")
        settings.validate()
        logger.info("✓ Configuration valid")
        
        # Initialize database
        logger.info("Initializing database...")
        self.db_manager = DatabaseManager(settings.DATABASE_URL)
        self.db_manager.create_tables()
        logger.info("✓ Database initialized")
        
        # Initialize clients
        logger.info("Initializing API clients...")
        self.twitter_client = TwitterClient()
        self.nba_client = NBAClient()
        logger.info("✓ API clients initialized")
        
        # Initialize agents based on enabled features
        logger.info("Initializing agents...")
        self.tweet_monitor = None
        self.box_score_agent = None
        
        if settings.ENABLE_TWEET_MONITORING:
            logger.info("  - Tweet monitoring is ENABLED")
            from analyzers import InjuryDetector
            self.injury_detector = InjuryDetector()
            self.tweet_monitor = TweetMonitorAgent(
                twitter_client=self.twitter_client,
                injury_detector=self.injury_detector,
                db_manager=self.db_manager,
                target_username=settings.SHAMS_TWITTER_USERNAME
            )
        else:
            logger.info("  - Tweet monitoring is DISABLED (set ENABLE_TWEET_MONITORING=true to enable)")
        
        if settings.ENABLE_BOX_SCORE_POSTING:
            logger.info("  - Box score posting is ENABLED")
            self.box_score_agent = BoxScoreAgent(
                twitter_client=self.twitter_client,
                nba_client=self.nba_client,
                db_manager=self.db_manager
            )
        else:
            logger.info("  - Box score posting is DISABLED")
        
        if not self.tweet_monitor and not self.box_score_agent:
            raise ValueError("At least one feature must be enabled (tweet monitoring or box score posting)")
        
        logger.info("✓ Agents initialized")
        
        # Initialize scheduler
        logger.info("Initializing scheduler...")
        self.scheduler = JobScheduler(
            tweet_monitor=self.tweet_monitor,
            box_score_agent=self.box_score_agent,
            tweet_check_interval_minutes=settings.TWEET_CHECK_INTERVAL,
            box_score_post_interval_minutes=settings.BOX_SCORE_POST_INTERVAL
        )
        logger.info("✓ Scheduler initialized")
        
        logger.info("=" * 60)
        logger.info("NBA Agent Setup Complete")
        logger.info("=" * 60)
    
    def start(self):
        """Start the NBA Agent."""
        try:
            self.setup()
            
            # Register signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start the scheduler
            self.scheduler.start()
            self.running = True
            
            logger.info("NBA Agent is now running!")
            if settings.ENABLE_TWEET_MONITORING:
                logger.info("Monitoring: @" + settings.SHAMS_TWITTER_USERNAME)
                logger.info("Tweet checks: every {} minutes".format(settings.TWEET_CHECK_INTERVAL))
            if settings.ENABLE_BOX_SCORE_POSTING:
                logger.info("Box score posts: every {} minutes".format(settings.BOX_SCORE_POST_INTERVAL))
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 60)
            
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.stop()
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            self.stop()
            sys.exit(1)
    
    def stop(self):
        """Stop the NBA Agent."""
        logger.info("=" * 60)
        logger.info("NBA Agent Shutting Down")
        logger.info("=" * 60)
        
        self.running = False
        
        if self.scheduler:
            self.scheduler.stop()
        
        logger.info("NBA Agent stopped successfully")
        logger.info("=" * 60)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point."""
    # Set up logging
    setup_logging()
    
    # Create and start the agent
    agent = NBAAgent()
    agent.start()


if __name__ == "__main__":
    main()

