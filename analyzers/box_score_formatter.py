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
        team_stats: Dict[int, List[Dict[str, Any]]]
    ) -> str:
        """
        Create a game summary with detailed player performances.
        
        Args:
            game_data: Dictionary containing game information
            team_stats: Dictionary of player stats by team
            
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
        winner = away_team if away_score > home_score else home_team
        tweet = f"🏀 FINAL: {away_team} {away_score}, {home_team} {home_score}\n\n"
        
        # Find notable performances from both teams
        notable_players = []
        
        for team_id, team_name in [(away_team_id, away_team), (home_team_id, home_team)]:
            if team_id not in team_stats:
                continue
                
            players = team_stats[team_id]
            
            # Get leading scorer
            leading_scorer = max(players, key=lambda x: x['points'])
            
            # Check for double-doubles and triple-doubles
            for player in players:
                stats = [player['points'], player['rebounds'], player['assists']]
                double_digit_stats = sum(1 for s in stats if s >= 10)
                
                # Check if this is leading scorer, double-double, or triple-double
                is_leader = player['player_name'] == leading_scorer['player_name']
                is_double_double = double_digit_stats >= 2
                is_triple_double = double_digit_stats >= 3
                has_notable_stat = player['rebounds'] >= 15 or player['assists'] >= 15
                
                if is_leader or is_triple_double or (is_double_double and has_notable_stat):
                    notable_players.append({
                        'team': team_name,
                        'player': player,
                        'is_triple_double': is_triple_double,
                        'is_double_double': is_double_double,
                        'is_leader': is_leader
                    })
        
        # Format notable performances
        if notable_players:
            for perf in notable_players[:3]:  # Max 3 players to fit in tweet
                player = perf['player']
                badges = []
                if perf['is_triple_double']:
                    badges.append("🔥 TRIPLE-DOUBLE")
                elif perf['is_double_double']:
                    badges.append("💪")
                
                badge_str = f" {badges[0]}" if badges else ""
                tweet += f"{perf['team']}: {player['player_name']}{badge_str}\n"
                tweet += f"{player['points']}pts/{player['rebounds']}reb/{player['assists']}ast"
                
                # Add notable stats
                if player['blocks'] >= 3:
                    tweet += f"/{player['blocks']}blk"
                if player['steals'] >= 3:
                    tweet += f"/{player['steals']}stl"
                
                tweet += "\n\n"
        
        # Remove trailing newlines and check length
        tweet = tweet.rstrip()
        
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

