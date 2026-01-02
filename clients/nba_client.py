"""
NBA API client for fetching game data and box scores.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv3, leaguegamefinder
from nba_api.stats.static import teams
from loguru import logger


class NBAClient:
    """Client for interacting with NBA API."""
    
    def __init__(self):
        """Initialize NBA client."""
        self.teams_data = teams.get_teams()
        
    def get_team_abbreviation(self, team_id: int) -> str:
        """
        Get team abbreviation from team ID.
        
        Args:
            team_id: NBA team ID
            
        Returns:
            Team abbreviation (e.g., 'LAL', 'BOS')
        """
        for team in self.teams_data:
            if team['id'] == team_id:
                return team['abbreviation']
        return "UNK"
    
    def get_team_name(self, team_id: int) -> str:
        """
        Get full team name from team ID.
        
        Args:
            team_id: NBA team ID
            
        Returns:
            Full team name (e.g., 'Los Angeles Lakers')
        """
        for team in self.teams_data:
            if team['id'] == team_id:
                return team['full_name']
        return "Unknown Team"
    
    def get_recent_games(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Get games from the past N days.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of game dictionaries
        """
        try:
            target_date = datetime.now() - timedelta(days=days_back)
            date_str = target_date.strftime("%Y-%m-%d")
            
            scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str)
            games_data = scoreboard.get_normalized_dict()
            
            games = []
            if 'GameHeader' in games_data:
                for game in games_data['GameHeader']:
                    games.append({
                        'game_id': game['GAME_ID'],
                        'game_date': game['GAME_DATE_EST'],
                        'home_team_id': game['HOME_TEAM_ID'],
                        'away_team_id': game['VISITOR_TEAM_ID'],
                        'home_team': self.get_team_abbreviation(game['HOME_TEAM_ID']),
                        'away_team': self.get_team_abbreviation(game['VISITOR_TEAM_ID']),
                        'game_status': game['GAME_STATUS_TEXT'],
                    })
            
            logger.info(f"Found {len(games)} games from {date_str}")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching recent games: {e}")
            return []
    
    def get_completed_games_today(self) -> List[Dict[str, Any]]:
        """
        Get all completed games from today.
        
        Returns:
            List of completed game dictionaries
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            scoreboard = scoreboardv2.ScoreboardV2(game_date=today)
            games_data = scoreboard.get_normalized_dict()
            
            games = []
            if 'GameHeader' in games_data and 'LineScore' in games_data:
                game_headers = {g['GAME_ID']: g for g in games_data['GameHeader']}
                
                for line in games_data['LineScore']:
                    game_id = line['GAME_ID']
                    
                    if game_id not in game_headers:
                        continue
                    
                    header = game_headers[game_id]
                    
                    # Only include completed games
                    if header['GAME_STATUS_TEXT'] != 'Final':
                        continue
                    
                    # Check if we already have this game
                    existing_game = next((g for g in games if g['game_id'] == game_id), None)
                    
                    if existing_game:
                        # Add score info
                        if line['TEAM_ID'] == header['HOME_TEAM_ID']:
                            existing_game['home_score'] = line['PTS']
                        else:
                            existing_game['away_score'] = line['PTS']
                    else:
                        # Create new game entry
                        game = {
                            'game_id': game_id,
                            'game_date': header['GAME_DATE_EST'],
                            'home_team_id': header['HOME_TEAM_ID'],
                            'away_team_id': header['VISITOR_TEAM_ID'],
                            'home_team': self.get_team_abbreviation(header['HOME_TEAM_ID']),
                            'away_team': self.get_team_abbreviation(header['VISITOR_TEAM_ID']),
                        }
                        
                        if line['TEAM_ID'] == header['HOME_TEAM_ID']:
                            game['home_score'] = line['PTS']
                        else:
                            game['away_score'] = line['PTS']
                        
                        games.append(game)
            
            logger.info(f"Found {len(games)} completed games today")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching completed games: {e}")
            return []
    
    def get_box_score(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed box score for a specific game.
        
        Args:
            game_id: NBA game ID
            
        Returns:
            Box score data dictionary or None if failed
        """
        try:
            box_score = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
            
            # V3 uses DataFrames instead of normalized dict
            dfs = box_score.get_data_frames()
            
            if not dfs or len(dfs) == 0:
                logger.error(f"No box score data found for game {game_id}")
                return None
            
            # First DataFrame contains player stats
            player_df = dfs[0]
            
            if player_df.empty:
                logger.error(f"Empty player stats for game {game_id}")
                return None
            
            # Group by team
            team_stats = {}
            
            for _, player in player_df.iterrows():
                team_id = player['teamId']
                if team_id not in team_stats:
                    team_stats[team_id] = []
                
                # Build player name from firstName and familyName
                player_name = f"{player.get('firstName', '')} {player.get('familyName', '')}".strip()
                
                team_stats[team_id].append({
                    'player_name': player_name,
                    'minutes': player.get('minutes', '0:00'),
                    'points': int(player.get('points', 0)),
                    'rebounds': int(player.get('reboundsTotal', 0)),
                    'assists': int(player.get('assists', 0)),
                    'steals': int(player.get('steals', 0)),
                    'blocks': int(player.get('blocks', 0)),
                    'fg_pct': float(player.get('fieldGoalsPercentage', 0)),
                    'three_pt_pct': float(player.get('threePointersPercentage', 0)),
                })
            
            logger.info(f"Successfully fetched box score for game {game_id}: {len(player_df)} players from {len(team_stats)} teams")
            
            return {
                'game_id': game_id,
                'team_stats': team_stats,
            }
            
        except Exception as e:
            logger.error(f"Error fetching box score for game {game_id}: {e}")
            return None
    
    def get_top_performers(self, game_id: str, top_n: int = 3) -> Optional[Dict[str, Any]]:
        """
        Get top performers from a game.
        
        Args:
            game_id: NBA game ID
            top_n: Number of top performers per team
            
        Returns:
            Dictionary with top performers per team
        """
        box_score = self.get_box_score(game_id)
        if not box_score:
            return None
        
        top_performers = {}
        
        for team_id, players in box_score['team_stats'].items():
            # Sort by points
            sorted_players = sorted(players, key=lambda x: x['points'], reverse=True)
            top_performers[team_id] = sorted_players[:top_n]
        
        return top_performers
    
    def get_all_players_stats(self, game_id: str) -> Optional[Dict[int, List[Dict[str, Any]]]]:
        """
        Get all player stats from a game, organized by team.
        
        Args:
            game_id: NBA game ID
            
        Returns:
            Dictionary with all player stats by team
        """
        box_score = self.get_box_score(game_id)
        if not box_score:
            return None
        
        return box_score.get('team_stats', {})

