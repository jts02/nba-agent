# NBA Box Score Bot - Usage Guide

## Quick Setup

### 1. Update Your `.env` File

Set the polling interval to check every minute:

```env
# Twitter credentials (you already have these)
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
TWITTER_BEARER_TOKEN=your_bearer

# Check for new games every minute
BOX_SCORE_POST_INTERVAL=1

# Enable box scores, disable tweet monitoring
ENABLE_BOX_SCORE_POSTING=true
ENABLE_TWEET_MONITORING=false

# Database (automatically tracks posted games)
DATABASE_URL=sqlite:///nba_agent.db

LOG_LEVEL=INFO
```

### 2. Run the Bot

```bash
python main.py
```

The bot will:
- ✅ Check for completed games **every minute**
- ✅ Post about NEW games only
- ✅ Track posted games in SQLite database (no Twitter API needed)
- ✅ Include detailed stats in posts

## What Gets Posted

For each completed game, the bot posts:

### Example Tweet Format:

```
🏀 FINAL: LAL 115, BOS 108

LAL: LeBron James
28pts/8reb/11ast

BOS: Jayson Tatum 🔥 TRIPLE-DOUBLE
32pts/10reb/12ast

LAL: Anthony Davis 💪
24pts/15reb/4ast
```

### Stats Included:

1. **Leading scorer from each team** (always included)
2. **Triple-doubles** 🔥 (10+ in 3 categories)
3. **Double-doubles** 💪 (10+ in 2 categories, IF also has 15+ rebounds or assists)
4. **Notable performances**: 15+ rebounds or 15+ assists

## How Duplicate Prevention Works

The bot uses a SQLite database (`nba_agent.db`) to track posted games:

- Each game has a unique `game_id` (e.g., `0022500471`)
- Before posting, the bot checks if this `game_id` exists in the database
- If found → Skip (already posted)
- If not found → Post and save to database

**No Twitter API calls needed** - everything is tracked locally!

## Database

The `nba_agent.db` file stores:
- All posted games with their IDs
- Timestamps of when they were posted
- The exact tweet text that was posted
- The Twitter tweet ID (for reference)

### View Posted Games

```bash
sqlite3 nba_agent.db "SELECT game_id, home_team, away_team, home_score, away_score, posted_at FROM box_score_posts ORDER BY posted_at DESC LIMIT 10;"
```

### Clear History (Re-post Everything)

⚠️ Only do this if you want to repost old games:

```bash
sqlite3 nba_agent.db "DELETE FROM box_score_posts;"
```

## Testing

### Test Without Posting

```bash
python test_boxscore.py
```

This shows you what would be posted without actually posting to Twitter.

### Test Auth

```bash
python test_twitter_auth.py
```

Verifies your Twitter credentials work.

## Running 24/7

### Option 1: Keep Terminal Open

Just leave it running:
```bash
python main.py
```

### Option 2: Run in Background (macOS/Linux)

```bash
nohup python main.py > output.log 2>&1 &
```

### Option 3: Use `screen` or `tmux`

```bash
# Create a screen session
screen -S nba-bot

# Run the bot
python main.py

# Detach: Press Ctrl+A then D
# Reattach later: screen -r nba-bot
```

### Option 4: System Service (Recommended for Production)

See `README.md` for systemd service setup instructions.

## Logs

Logs are saved in `logs/` directory:

```bash
# View today's log
tail -f logs/nba_agent_$(date +%Y-%m-%d).log

# Search for errors
grep ERROR logs/nba_agent_*.log

# View posted games
grep "Successfully posted box score" logs/nba_agent_*.log
```

## Customization

### Change Polling Interval

Edit `.env`:
```env
BOX_SCORE_POST_INTERVAL=1   # Every minute (default)
BOX_SCORE_POST_INTERVAL=5   # Every 5 minutes
BOX_SCORE_POST_INTERVAL=10  # Every 10 minutes
```

### Adjust Stats Criteria

Edit `analyzers/box_score_formatter.py`:

```python
# Current: 15+ rebounds or assists is notable
has_notable_stat = player['rebounds'] >= 15 or player['assists'] >= 15

# Change to 20+
has_notable_stat = player['rebounds'] >= 20 or player['assists'] >= 20

# Add steals/blocks
has_notable_stat = (player['rebounds'] >= 15 or 
                   player['assists'] >= 15 or
                   player['steals'] >= 5 or
                   player['blocks'] >= 5)
```

### Change Tweet Format

Edit `analyzers/box_score_formatter.py` in the `format_game_with_top_performers()` method.

## Troubleshooting

### "No completed games found"
- This is normal if no games have finished yet
- The bot checks every minute, so it will post when games complete

### "Already posted"
- The bot correctly skipped a duplicate game
- Check database: `sqlite3 nba_agent.db "SELECT * FROM box_score_posts;"`

### Bot not posting
1. Check logs: `tail -f logs/nba_agent_*.log`
2. Verify Twitter auth: `python test_twitter_auth.py`
3. Check if games are actually completed
4. Make sure `.env` has `ENABLE_BOX_SCORE_POSTING=true`

### Want to repost a game
Delete it from the database:
```bash
sqlite3 nba_agent.db "DELETE FROM box_score_posts WHERE game_id='0022500471';"
```

## Example Workflow

**During an NBA game night:**

1. Start the bot: `python main.py`
2. Bot checks every minute for completed games
3. When a game finishes, bot immediately posts detailed stats
4. Game is saved to database
5. Bot continues checking for more games
6. All games are posted once and only once

**Next day:**

- Bot remembers what was posted (it's in the database)
- Won't repost yesterday's games
- Only posts NEW completed games

## Stop the Bot

Press `Ctrl+C` in the terminal where it's running.

The bot will gracefully shutdown:
```
^C
2026-01-01 14:30:00 | INFO     | Received keyboard interrupt
============================================================
NBA Agent Shutting Down
============================================================
```

---

That's it! The bot handles everything automatically - just set it and forget it! 🏀🤖

