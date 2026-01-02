"""
Formatter for creating engaging box score posts.
"""
from typing import Dict, Any, List
from loguru import logger


class BoxScoreFormatter:
    """Format box score data into tweet-ready content."""
    
    @staticmethod
    def format_game_summary(game_data: Dict[str, Any]) -> str:
        """
        Create a concise game summary for Twitter.
        
        Args:
            game_data: Dictionary containing game information
            
        Returns:
            Formatted tweet text
        """
        away_team = game_data.get('away_team', 'AWAY')
        home_team = game_data.get('home_team', 'HOME')
        away_score = game_data.get('away_score', 0)
        home_score = game_data.get('home_score', 0)
        
        # Determine winner
        if away_score > home_score:
            winner = away_team
            loser = home_team
            winner_score = away_score
            loser_score = home_score
        else:
            winner = home_team
            loser = away_team
            winner_score = home_score
            loser_score = away_score
        
        # Create tweet
        tweet = f"🏀 FINAL SCORE\n\n"
        tweet += f"{away_team} {away_score} @ {home_team} {home_score}\n\n"
        tweet += f"{winner} wins {winner_score}-{loser_score}! 🎯"
        
        return tweet
    
    @staticmethod
    def format_game_with_top_performers(
        game_data: Dict[str, Any],
        top_performers: Dict[int, List[Dict[str, Any]]]
    ) -> str:
        """
        Create a game summary with top performers.
        
        Args:
            game_data: Dictionary containing game information
            top_performers: Dictionary of top performers by team
            
        Returns:
            Formatted tweet text
        """
        away_team = game_data.get('away_team', 'AWAY')
        home_team = game_data.get('home_team', 'HOME')
        away_score = game_data.get('away_score', 0)
        home_score = game_data.get('home_score', 0)
        away_team_id = game_data.get('away_team_id')
        home_team_id = game_data.get('home_team_id')
        
        # Start with score
        tweet = f"🏀 FINAL: {away_team} {away_score}, {home_team} {home_score}\n\n"
        
        # Add top performers
        tweet += "⭐ Top Performers:\n\n"
        
        # Away team top performer
        if away_team_id in top_performers and top_performers[away_team_id]:
            top_away = top_performers[away_team_id][0]
            tweet += f"{away_team}: {top_away['player_name']}\n"
            tweet += f"  {top_away['points']}pts, {top_away['rebounds']}reb, {top_away['assists']}ast\n\n"
        
        # Home team top performer
        if home_team_id in top_performers and top_performers[home_team_id]:
            top_home = top_performers[home_team_id][0]
            tweet += f"{home_team}: {top_home['player_name']}\n"
            tweet += f"  {top_home['points']}pts, {top_home['rebounds']}reb, {top_home['assists']}ast"
        
        # Truncate if too long
        if len(tweet) > 280:
            logger.warning("Tweet too long, using simpler format")
            return BoxScoreFormatter.format_game_summary(game_data)
        
        return tweet
    
    @staticmethod
    def format_multiple_games(games: List[Dict[str, Any]]) -> str:
        """
        Format multiple game scores into a single tweet.
        
        Args:
            games: List of game dictionaries
            
        Returns:
            Formatted tweet text
        """
        if not games:
            return ""
        
        if len(games) == 1:
            return BoxScoreFormatter.format_game_summary(games[0])
        
        tweet = f"🏀 NBA SCORES ({len(games)} games)\n\n"
        
        for game in games[:5]:  # Max 5 games to fit in tweet
            away = game.get('away_team', 'AWAY')
            home = game.get('home_team', 'HOME')
            away_score = game.get('away_score', 0)
            home_score = game.get('home_score', 0)
            
            tweet += f"{away} {away_score} @ {home} {home_score}\n"
        
        if len(games) > 5:
            tweet += f"\n... and {len(games) - 5} more games"
        
        # Truncate if needed
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."
        
        return tweet

