"""
Configuration settings for the NBA Agent.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Twitter API Credentials
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    
    # OpenAI API Key (optional - only needed for tweet monitoring)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Target Account (optional - only needed for tweet monitoring)
    SHAMS_TWITTER_USERNAME = os.getenv("SHAMS_TWITTER_USERNAME", "ShamsCharania")
    
    # Feature flags
    ENABLE_TWEET_MONITORING = os.getenv("ENABLE_TWEET_MONITORING", "false").lower() == "true"
    ENABLE_BOX_SCORE_POSTING = os.getenv("ENABLE_BOX_SCORE_POSTING", "true").lower() == "true"
    
    # Scheduling Configuration (in minutes)
    TWEET_CHECK_INTERVAL = int(os.getenv("TWEET_CHECK_INTERVAL", "5"))
    BOX_SCORE_POST_INTERVAL = int(os.getenv("BOX_SCORE_POST_INTERVAL", "60"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nba_agent.db")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Validate that all required settings are present."""
        # Always required for Twitter posting
        required_settings = [
            "TWITTER_API_KEY",
            "TWITTER_API_SECRET",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET",
            "TWITTER_BEARER_TOKEN",
        ]
        
        # Only required if tweet monitoring is enabled
        if cls.ENABLE_TWEET_MONITORING:
            required_settings.append("OPENAI_API_KEY")
        
        missing = []
        for setting in required_settings:
            if not getattr(cls, setting):
                missing.append(setting)
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        return True


settings = Settings()

