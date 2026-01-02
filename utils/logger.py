"""
Logging configuration for the NBA Agent.
"""
import sys
from loguru import logger
from config import settings


def setup_logging():
    """Configure logging for the application."""
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # Add file handler for persistent logs
    logger.add(
        "logs/nba_agent_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # Rotate at midnight
        retention="30 days",  # Keep logs for 30 days
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level="DEBUG",
        compression="zip"  # Compress old logs
    )
    
    logger.info("Logging configured successfully")

