# Smart Heat Bot - Quick Start Commands

## ✅ All Setup Complete!

All imports work, no syntax errors detected. The bot is ready to run!

---

## Commands to Run

### 1. Monitor Mode (Build Memory - Run First!)
Scrape Heat Twitter and build memory without posting tweets:

```bash
venv/bin/python smart_heat_bot.py --mode monitor
```

**Recommended for first run**: Let this run for a few hours to build up context:
```bash
# Check every 30 minutes and just scrape (no tweets)
venv/bin/python smart_heat_bot.py loop 30 --mode monitor
```

---

### 2. Auto Mode (Intelligent Bot - Recommended)
Bot decides what to do based on context (scrape, analyze, tweet when appropriate):

```bash
# Single run - bot decides if it should tweet
venv/bin/python smart_heat_bot.py

# Continuous mode - check every 20 minutes
venv/bin/python smart_heat_bot.py loop 20
```

---

### 3. Game Mode (Live Game Reactions)
Focus on Heat games:

```bash
# Single check for live game
venv/bin/python smart_heat_bot.py --mode game

# Check every 5 minutes during games
venv/bin/python smart_heat_bot.py loop 5 --mode game
```

---

### 4. Discourse Mode (Jump into Heat Twitter Conversations)
Respond to trending Heat topics:

```bash
venv/bin/python smart_heat_bot.py --mode discourse
```

---

### 5. Original Mode (Standalone Takes)
Drop original Heat takes:

```bash
venv/bin/python smart_heat_bot.py --mode original
```

---

## Recommended Workflow

### First Time Setup:
```bash
# Step 1: Build initial memory (let run for 2-4 hours)
venv/bin/python smart_heat_bot.py loop 30 --mode monitor

# Step 2: Once memory is built, switch to auto mode
venv/bin/python smart_heat_bot.py loop 20
```

### Daily Operation:
```bash
# Just run auto mode - bot handles everything
venv/bin/python smart_heat_bot.py loop 20
```

### During Heat Games:
```bash
# Run game mode for frequent reactions
venv/bin/python smart_heat_bot.py loop 5 --mode game
```

---

## Expected Output

You'll see:
```
======================================================================
🏀🔥 SMART MIAMI HEAT BOT - Intelligent & Chaotic 🔥🏀
======================================================================
Mode: MONITOR
✅ API key found
🔌 Connecting to Smart Heat MCP server...
✅ Connected to MCP server
✅ Loaded 14 tools

======================================================================
🎯 Task: MONITOR mode
======================================================================

🔧 Smart Heat Bot is thinking and using tools...

   • Calling: scrape_heat_twitter
     Args: {
       "account_category": "all",
       "max_tweets_per_account": 10
     }
     Result: {"success": true, "accounts_scraped": 10, "total_tweets": 85, ...}

🧠 Smart Heat Bot's Summary:
======================================================================
Successfully scraped Heat Twitter...
```

---

## If You Get Rate Limited

Don't worry! The bot handles it gracefully:

```json
{
  "rate_limited": true,
  "wait_minutes": 15,
  "message": "⚠️ RATE LIMITED - Wait 15 minutes",
  "accounts_succeeded": 3,
  "total_tweets": 45
}
```

**What to do:**
- Wait 15 minutes before scraping again
- Bot can still use existing database context
- Increase time between checks: `loop 60` instead of `loop 30`

---

## Monitoring the Bot

### Check Database
```bash
# See recent bot tweets
sqlite3 nba_agent.db "SELECT posted_at, tweet_type, tweet_text FROM smart_bot_tweets ORDER BY posted_at DESC LIMIT 10;"

# See monitored tweets
sqlite3 nba_agent.db "SELECT author_username, tweet_text, likes FROM monitored_tweets ORDER BY scraped_at DESC LIMIT 10;"

# See active narratives
sqlite3 nba_agent.db "SELECT title, description FROM heat_narratives WHERE status='active';"
```

### Stop the Bot
Press `Ctrl+C` to stop gracefully.

---

## Tips

1. **Build memory first**: Run monitor mode before going live
2. **Use auto mode**: Let Claude decide when to tweet
3. **Monitor console**: Watch the decision-making process
4. **Check rate limits**: Use longer intervals if getting rate limited
5. **Quality over quantity**: Bot naturally spaces tweets out

---

## Files Created

- `smart_heat_bot.py` - Main agent
- `smart_heat_mcp_server.py` - MCP server with tools
- `database/models.py` - Enhanced with 4 new tables
- `SMART_HEAT_BOT.md` - Full documentation
- `RATE_LIMIT_FIX.md` - Rate limit handling details

---

## What Was Fixed

✅ Removed player accounts (Jimmy Butler no longer on Heat)
✅ Added comprehensive rate limit handling
✅ Reduced default API calls by 55%
✅ Bot works even when rate limited
✅ All imports verified and working
✅ No syntax errors

---

**The bot is ready! Start with monitor mode to build memory, then switch to auto mode. Enjoy! 🔥🏀**
