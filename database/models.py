"""
Database models for tracking tweets and posts.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class ProcessedTweet(Base):
    """Track tweets that have been processed to avoid duplicates."""
    
    __tablename__ = "processed_tweets"
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(50), unique=True, nullable=False, index=True)
    author_username = Column(String(100), nullable=False)
    tweet_text = Column(Text, nullable=False)
    is_injury_related = Column(Boolean, default=False)
    reposted = Column(Boolean, default=False)
    repost_id = Column(String(50), nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ProcessedTweet(tweet_id='{self.tweet_id}', is_injury={self.is_injury_related})>"


class BoxScorePost(Base):
    """Track box score posts to avoid duplicate postings."""
    
    __tablename__ = "box_score_posts"
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String(50), unique=True, nullable=False, index=True)
    game_date = Column(DateTime, nullable=False)
    home_team = Column(String(50), nullable=False)
    away_team = Column(String(50), nullable=False)
    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    post_text = Column(Text, nullable=False)
    tweet_id = Column(String(50), nullable=True)
    posted_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BoxScorePost(game_id='{self.game_id}', {self.away_team}@{self.home_team})>"


class AgentLog(Base):
    """Log agent activities for monitoring and debugging."""
    
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    log_level = Column(String(20), nullable=False)
    component = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    error_details = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<AgentLog({self.log_level}: {self.component})>"


class DatabaseManager:
    """Manage database connections and operations."""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
    
    def drop_tables(self):
        """Drop all tables (use with caution)."""
        Base.metadata.drop_all(self.engine)

