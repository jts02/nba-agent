# 🔥 Miami Heat Fan Bot - Extremely Opinionated Live Game Commentary

## Overview

This is a **completely separate bot** from the main NBA agent. While the main agent posts professional box scores and injury reports, this bot is an **unhinged Miami Heat superfan** that posts controversial, emotional takes during live Heat games.

## What It Does

- **Monitors live Heat games** in real-time
- **Compares box scores** between checks to see what changed
- **Posts spicy tweets** reacting to player performance:
  - **Roasts players** brutally when they mess up (missed shots, turnovers)
  - **Praises players** with wild exaggeration when they do well
  - Uses creative insults, ALL CAPS, emojis, and zero chill

## Files

### Production Files
- `heat_fan_agent.py` - The AI agent with unhinged personality
- `heat_fan_mcp_server.py` - MCP server with live game tools

### Test Files
- `test_heat_fan_mcp_server.py` - Test server with dummy evolving game data

## Installation

All dependencies are already installed from the main bot:
```bash
# Already have these from requirements.txt:
# - nba_api
# - tweepy
# - anthropic
# - sqlalchemy
# - loguru
```

## Usage

### Test Mode (Recommended First)

Test mode uses dummy data that evolves to simulate different scenarios:
- **Check 1**: First baseline snapshot (no tweet)
- **Check 2**: Bam misses 3 shots in a row → Bot roasts him
- **Check 3**: Jimmy scores 10 points → Bot praises wildly
- **Check 4**: Tyler Herro bricks 5 shots → More roasting
- **Check 5**: Bam has a redemption arc → Bot forgives him

**Important:** Use **loop mode** to see multiple checks and tweets! Single runs only save the first snapshot.

```bash
# RECOMMENDED: Continuous mode - checks every 1 minute (to see tweets quickly)
python heat_fan_agent.py loop 1 --test

# Press Ctrl+C after seeing a few tweets (5-10 minutes)

# Or check every 3 minutes
python heat_fan_agent.py loop 3 --test
```

### Production Mode (Live Games)

```bash
# Single check for live Heat game
python heat_fan_agent.py

# Continuous mode - checks every 3 minutes (recommended during games)
python heat_fan_agent.py loop 3

# Check every 5 minutes
python heat_fan_agent.py loop 5
```

## Bot Personality

The bot uses Claude with this personality:

### Roasting Examples (when players mess up):
```
"BAM BRICKED 3 STRAIGHT 🤡 BENCH THIS MAN"

"TYLER HER-NO CANT HIT ANYTHING 🗑️ 0-5 GET HIM OUT"

"Bam Ade-brick-o strikes again 💀 TRADE HIM"
```

### Praising Examples (when players do well):
```
"JIMMY IS LITERALLY MJ 🔥🔥🔥 20 PTS THIS QUARTER"

"BAM IS THE GREATEST CENTER ALIVE 👑 UNSTOPPABLE"

"TYLER HERRO ON FIRE 💪 3/3 FROM THREE HE'S HIM"
```

**Note:** Tweets are kept SHORT (100-150 chars) for maximum shitpost energy!

## How It Works

### 1. Check for Live Game
```python
get_live_heat_game()  # Returns game info if Heat are playing
```

### 2. Get Current Box Score
```python
get_heat_box_score(game_id)  # Returns all Heat player stats
```

### 3. Compare to Last Snapshot
```python
compare_box_scores(game_id, current_stats)
# Returns what changed since last check:
# - Points added/missed shots
# - Rebounds/assists/turnovers
```

### 4. Analyze & React
Claude analyzes the changes with its opinionated personality:
- **3+ missed shots** → Roast the player
- **6+ points added** → Praise wildly  
- **Multiple turnovers** → Question their existence
- **Dominant performance** → Crown them as GOAT

### 5. Post Tweet
```python
post_heat_tweet(tweet_text, game_id, snapshot_id)
```

### 6. Save Snapshot
```python
save_snapshot(...)  # Save current state for next comparison
```

## Database

The bot uses a new table `live_game_snapshots` to track:
- Game state at each check (score, period, clock)
- Full box score JSON for comparison
- Tweet IDs for posted reactions
- Timestamps to prevent spam

## Safety Features

### Rate Limiting
- Won't tweet more than once every 5 minutes (configurable)
- Uses `check_recent_heat_tweets()` to prevent spam

### Smart Tweeting
- Only tweets when something **interesting** happened
- Ignores minor stat changes
- Requires significant events (big runs, meltdowns, etc.)

## Running Both Bots

You can run the Heat fan bot AND the main NBA agent simultaneously:

```bash
# Terminal 1: Main NBA agent (box scores + injuries)
python ai_agent.py loop 5

# Terminal 2: Heat fan bot (live game reactions)
python heat_fan_agent.py loop 3
```

They use separate:
- MCP servers
- Database tables  
- Tweet posting logic

No conflicts!

## Example Output

```
============================================================
🔥 MIAMI HEAT FAN BOT - EXTREMELY OPINIONATED 🔥
============================================================
✅ API key found
🔌 Connecting to Heat Fan MCP server (LIVE)...
✅ Connected to MCP server
✅ Loaded 6 tools

============================================================
🎯 Checking for live Heat game...
============================================================

🔧 Heat Fan Bot is checking stats...

============================================================
🔥 WOULD POST TWEET:
============================================================
BAM ADEBAYO JUST MISSED 3 SHOTS IN A ROW 🤡 0 POINTS ON 0-3 
SHOOTING MY EYES ARE BLEEDING someone tell him this is 
basketball not volleyball 🗑️💀
============================================================

============================================================
🔥 Heat Fan's Take:
============================================================
BAM IS SELLING RIGHT NOW! Just posted my take on Twitter. 
This man better turn it around in the 2nd half or I'm 
calling for a trade! 😤🔥
============================================================
```

## Customization

### Change Personality
Edit the `system_prompt` in `heat_fan_agent.py` (lines 69-130) to adjust:
- Tone (more/less aggressive)
- Emoji usage
- Roasting vs praising threshold
- Language style

### Change Check Interval
```bash
# Check every 2 minutes (more reactive)
python heat_fan_agent.py loop 2

# Check every 10 minutes (less spam)
python heat_fan_agent.py loop 10
```

### Add More Players
The bot automatically detects all Heat players from the box score. No configuration needed.

## Tips

1. **Run in loop mode during games**: `python heat_fan_agent.py loop 3`
2. **Test first**: Always test with `--test` to see personality
3. **Monitor terminal**: Watch Claude's reasoning in real-time
4. **Adjust interval**: 3-5 minutes is good for live games
5. **Check database**: SQLite `live_game_snapshots` table shows history

## Troubleshooting

### "No live Heat game"
- Heat aren't playing right now
- Or game hasn't started yet (pre-game)
- Or game is already finished

### Bot not tweeting
- Nothing interesting changed since last check
- Or recently tweeted (5 min cooldown)
- Or first check (needs baseline snapshot)

### "Rate limit exceeded"
- Twitter API rate limit hit
- Wait or reduce check frequency

## Advanced: Modify Scenarios

Edit `test_heat_fan_mcp_server.py` to create custom test scenarios:

```python
# Line 43-62: Modify PLAYER_STATS evolution
elif check == 6:
    # Create your own scenario
    PLAYER_STATS["Jimmy Butler"]["points"] += 15  # Jimmy goes nuclear
    PLAYER_STATS["Bam Adebayo"]["turnovers"] += 3  # Bam disaster
```

Then run with `--test` to see bot's reaction!

## Production Recommendations

1. Run during Heat games only (auto-detects)
2. Use 3-5 minute intervals
3. Monitor first few runs to tune personality
4. Have fun with it! 🔥

## Comparison to Main Bot

| Feature | Main NBA Agent | Heat Fan Bot |
|---------|---------------|--------------|
| **Focus** | All NBA teams | Miami Heat only |
| **Tone** | Professional | Unhinged |
| **Timing** | Completed games | Live games |
| **Frequency** | Once per game | Every 3-5 min |
| **Purpose** | Info/stats | Entertainment/reaction |
| **Injuries** | Yes | No |
| **Box Scores** | Final | Live updates |

Both bots can run simultaneously without conflicts!

