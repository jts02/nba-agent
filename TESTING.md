# Testing Guide

## Quick Test with Dummy Data

Test your agent without waiting for real NBA games!

### Test Data

Two dummy games are included in `test_data.json`:

1. **LAL @ BOS (115-108)**
   - LeBron James: 32pts/12reb/11ast 🔥 TRIPLE-DOUBLE
   - Jayson Tatum: 35pts/8reb/6ast
   - Anthony Davis: 28pts/15reb/4ast 💪

2. **GSW @ PHX (98-112)**
   - Stephen Curry: 42pts/5reb/7ast
   - Devin Booker: 31pts/8reb/10ast 💪
   - Kevin Durant: 28pts/11reb/6ast

### Run Test Mode

```bash
# Run once with test data
python ai_agent.py test

# Or use --test flag
python ai_agent.py --test

# Run in loop mode with test data (check every 1 minute)
python ai_agent.py loop 1 --test
```

### What Happens in Test Mode

1. ✅ Uses `test_mcp_server.py` instead of `mcp_server.py`
2. ✅ Returns dummy games from `test_data.json`
3. ✅ Real Twitter posting (but adds "🧪 TEST POST" marker)
4. ✅ Real database tracking
5. ✅ Real Claude API calls

**Perfect for testing the full flow!**

### Verify Test Data

```bash
# Check what games are available
python -c "
import json
with open('test_data.json') as f:
    data = json.load(f)
    for game in data['games']:
        print(f\"Game {game['game_id']}: {game['away_team']} @ {game['home_team']} ({game['away_score']}-{game['home_score']})\")
"
```

### Clean Up Test Posts

```bash
# Delete test posts from database
sqlite3 nba_agent.db "DELETE FROM box_score_posts WHERE game_id LIKE '002250099%';"

# Or view them first
sqlite3 nba_agent.db "SELECT game_id, away_team, home_team, tweet_id FROM box_score_posts WHERE game_id LIKE '002250099%';"
```

### Example Test Run

```bash
$ python ai_agent.py test

============================================================
🧪 TEST MODE (Using dummy data)
============================================================
✅ API key found
🔌 Connecting to MCP server (TEST)...
✅ Connected to MCP server
✅ Loaded 8 tools

============================================================
🎯 Task: Check for NBA games and post interesting ones
============================================================

🔧 Claude is using tools...
   • Calling: check_for_new_games
     Result: {"total_completed": 2, "new_games": [...]}

🔧 Claude is using tools...
   • Calling: generate_custom_tweet
     Args: {"game_id": "0022500999"}
     Result: {...}

🔧 Claude is using tools...
   • Calling: post_custom_tweet
     Args: {"game_id": "0022500999", "tweet_text": "..."}

📝 Claude's Summary:
I found 2 test games. I posted the Lakers vs Celtics game because
LeBron had an incredible triple-double (32/12/11). The Warriors game
had great individual performances but was a blowout.
```

### Creating Your Own Test Data

Edit `test_data.json`:

```json
{
  "games": [
    {
      "game_id": "0022500999",
      "game_date": "2026-01-03T00:00:00",
      "away_team": "LAL",
      "home_team": "BOS",
      "away_team_id": 1610612737,
      "home_team_id": 1610612738,
      "away_score": 115,
      "home_score": 108,
      "player_stats": {
        "1610612737": [
          {
            "player_name": "Player Name",
            "points": 30,
            "rebounds": 10,
            "assists": 10,
            ...
          }
        ]
      }
    }
  ]
}
```

### Test Mode vs Production

| Feature | Test Mode | Production |
|---------|-----------|------------|
| **Data Source** | `test_data.json` | Real NBA API |
| **MCP Server** | `test_mcp_server.py` | `mcp_server.py` |
| **Twitter** | Real (with TEST marker) | Real |
| **Database** | Real | Real |
| **Claude API** | Real | Real |
| **Cost** | Same | Same |

### Tips

- ✅ Test mode is perfect for development
- ✅ Use test mode to verify Claude's tweet generation
- ✅ Test mode posts are marked with "🧪 TEST POST"
- ✅ You can delete test posts from database easily
- ✅ Test mode uses same database - posts are tracked normally

### Troubleshooting Test Mode

**"FileNotFoundError: test_data.json"**
```bash
# Make sure you're in the project directory
cd /Users/jacobtie-shue/Desktop/Projects/nba-agent
python ai_agent.py test
```

**"ModuleNotFoundError: test_mcp_server"**
- Test mode uses `test_mcp_server.py` - make sure it exists
- It should be in the same directory as `mcp_server.py`

**Test posts cluttering database**
```bash
# Clean them up
sqlite3 nba_agent.db "DELETE FROM box_score_posts WHERE game_id LIKE '002250099%';"
```

---

**Happy Testing!** 🧪🏀

