"""
AI-powered injury detection analyzer using Claude (Anthropic).
"""
from typing import Dict, Any, Optional
from anthropic import Anthropic
from loguru import logger
from config import settings
import json


class InjuryDetector:
    """Detect injury-related content in tweets using AI."""
    
    def __init__(self):
        """Initialize the injury detector with Claude client."""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
    def is_injury_related(self, tweet_text: str) -> Dict[str, Any]:
        """
        Analyze if a tweet is related to NBA player injuries.
        
        Args:
            tweet_text: The text of the tweet to analyze
            
        Returns:
            Dictionary with 'is_injury': bool, 'confidence': float, 'summary': str
        """
        try:
            prompt = f"""You are analyzing a tweet from an NBA insider to determine if it reports a player injury or injury-related news.

Tweet: "{tweet_text}"

MARK AS INJURY (is_injury: true) if the tweet mentions:
- Player is injured, hurt, or suffers an injury
- Player will miss games due to injury
- Player is out/questionable/doubtful/probable due to injury
- Medical updates: MRI, surgery, medical procedures for injuries
- Injury diagnosis: sprains, strains, fractures, tears, etc.
- Timeline for return from injury
- Re-evaluation timelines (e.g., "will be re-evaluated in X weeks")

DO NOT mark as injury if:
- Player is resting (not injured)
- General team news or trades
- Contract signings
- Player returning from injury (already healed) - UNLESS it specifically mentions timeline or injury details

Respond with ONLY a JSON object (no other text):
{{
    "is_injury": true or false,
    "confidence": 0.0 to 1.0 (how certain you are),
    "summary": "brief explanation of your decision"
}}

Be liberal with marking injuries - if there's any mention of a player being hurt or injured, mark it as injury-related."""
            
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.content[0].text.strip()
            
            # Parse JSON response
            result = json.loads(result_text)
            
            logger.info(
                f"Injury analysis: {result['is_injury']} "
                f"(confidence: {result['confidence']}) - {result['summary']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing tweet for injuries: {e}")
            # Return conservative default
            return {
                "is_injury": False,
                "confidence": 0.0,
                "summary": f"Error during analysis: {str(e)}"
            }
    
    def generate_repost_comment(self, original_tweet: str) -> Optional[str]:
        """
        Generate a brief comment for reposting an injury tweet.
        
        Args:
            original_tweet: The original tweet text
            
        Returns:
            Generated comment text or None if failed
        """
        try:
            prompt = f"""Generate a very brief comment (max 50 characters) for this injury news tweet.
Be professional and informative.

Examples: "Injury Update 🏀", "Breaking: Injury News", "Latest Injury Report"

Tweet: {original_tweet}

Respond with ONLY the comment text, nothing else."""
            
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=30,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            comment = response.content[0].text.strip()
            
            # Remove quotes if present
            if comment.startswith('"') and comment.endswith('"'):
                comment = comment[1:-1]
            
            logger.info(f"Generated comment: {comment}")
            return comment
            
        except Exception as e:
            logger.error(f"Error generating repost comment: {e}")
            return "🏀 Injury Update"

