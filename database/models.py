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


class MonitoredTweet(Base):
    """Track tweets from Heat Twitter accounts for learning and context."""

    __tablename__ = "monitored_tweets"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(50), unique=True, nullable=False, index=True)
    author_username = Column(String(100), nullable=False, index=True)
    author_display_name = Column(String(200), nullable=True)
    tweet_text = Column(Text, nullable=False)
    tweet_type = Column(String(50), nullable=False)  # original, reply, quote, retweet

    # Engagement metrics
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)

    # Context
    is_heat_related = Column(Boolean, default=True)
    sentiment = Column(String(20), nullable=True)  # positive, negative, neutral, chaotic
    topics = Column(Text, nullable=True)  # JSON list of topics (game reaction, trade rumor, etc)

    # Metadata
    scraped_at = Column(DateTime, default=datetime.utcnow)
    tweet_created_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<MonitoredTweet(@{self.author_username}: {self.tweet_text[:50]}...)>"


class HeatNarrative(Base):
    """Track ongoing Heat storylines and narratives."""

    __tablename__ = "heat_narratives"

    id = Column(Integer, primary_key=True)
    narrative_key = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)  # active, resolved, dormant

    # Context
    player_names = Column(Text, nullable=True)  # JSON list
    related_topics = Column(Text, nullable=True)  # JSON list

    # Timeline
    started_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Evidence
    supporting_tweet_ids = Column(Text, nullable=True)  # JSON list

    def __repr__(self):
        return f"<HeatNarrative('{self.title}' - {self.status})>"


class HeatKnowledge(Base):
    """Store facts about Heat players, team history, and context."""

    __tablename__ = "heat_knowledge"

    id = Column(Integer, primary_key=True)
    knowledge_key = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)  # player_stat, team_history, inside_joke, etc
    subject = Column(String(200), nullable=False)  # Player name, event, etc
    fact = Column(Text, nullable=False)

    # Sourcing
    source_type = Column(String(50), nullable=True)  # tweet, article, game_stat, manual
    source_id = Column(String(100), nullable=True)
    confidence = Column(Integer, default=100)  # 0-100

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_verified = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<HeatKnowledge({self.category}: {self.subject})>"


class SmartBotTweet(Base):
    """Track smart Heat bot's tweets and their performance."""

    __tablename__ = "smart_bot_tweets"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(50), unique=True, nullable=False, index=True)
    tweet_text = Column(Text, nullable=False)
    tweet_type = Column(String(50), nullable=False)  # game_reaction, discourse_reply, original_take, nostalgia

    # Context at time of posting
    context_used = Column(Text, nullable=True)  # JSON of narratives/knowledge used
    related_game_id = Column(String(50), nullable=True)
    reply_to_tweet_id = Column(String(50), nullable=True)

    # Performance tracking
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    impressions = Column(Integer, default=0)

    # Analysis
    performance_score = Column(Integer, nullable=True)  # 0-100 calculated score
    worked_well = Column(Boolean, nullable=True)  # Manual or auto flag

    # Metadata
    posted_at = Column(DateTime, default=datetime.utcnow)
    last_metrics_update = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<SmartBotTweet({self.tweet_type}: {self.tweet_text[:50]}...)>"


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

