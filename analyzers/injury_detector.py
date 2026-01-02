"""
AI-powered injury detection analyzer using OpenAI.
"""
from typing import Dict, Any, Optional
from openai import OpenAI
from loguru import logger
from config import settings


class InjuryDetector:
    """Detect injury-related content in tweets using AI."""
    
    def __init__(self):
        """Initialize the injury detector with OpenAI client."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def is_injury_related(self, tweet_text: str) -> Dict[str, Any]:
        """
        Analyze if a tweet is related to NBA player injuries.
        
        Args:
            tweet_text: The text of the tweet to analyze
            
        Returns:
            Dictionary with 'is_injury': bool, 'confidence': float, 'summary': str
        """
        try:
            system_prompt = """You are an NBA injury news analyst. Your job is to determine if a tweet 
            contains information about NBA player injuries, including:
            - Injury reports (player X is out/injured)
            - Injury updates (player X is questionable/probable/doubtful)
            - Return from injury announcements
            - Injury severity descriptions
            - Medical procedures related to injuries
            
            Respond ONLY with a JSON object in this exact format:
            {
                "is_injury": true/false,
                "confidence": 0.0-1.0,
                "summary": "brief explanation"
            }
            
            Do not include any other text outside the JSON object."""
            
            user_prompt = f"""Analyze this tweet and determine if it's injury-related:

Tweet: "{tweet_text}"

Respond with JSON only."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON response
            import json
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
            system_prompt = """You are an NBA news bot. Generate a very brief (max 50 characters) 
            comment to add context to injury news. Be professional and informative.
            Examples: "Injury Update 🏀", "Breaking: Injury News", "Latest Injury Report"
            
            Respond with ONLY the comment text, nothing else."""
            
            user_prompt = f"Generate a brief comment for this injury news:\n\n{original_tweet}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=30
            )
            
            comment = response.choices[0].message.content.strip()
            
            # Remove quotes if present
            if comment.startswith('"') and comment.endswith('"'):
                comment = comment[1:-1]
            
            logger.info(f"Generated comment: {comment}")
            return comment
            
        except Exception as e:
            logger.error(f"Error generating repost comment: {e}")
            return "🏀 Injury Update"

