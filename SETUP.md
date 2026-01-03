# NBA Agent - Complete Setup & Usage Guide

**Your AI-powered NBA Twitter bot with custom tweet generation!**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [How It Works](#how-it-works)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Agent](#running-the-agent)
6. [Making It Autonomous](#making-it-autonomous)
7. [Features](#features)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

**3 commands to get started:**

```bash
# 1. Install
pip install -r requirements.txt
pip install anthropic

# 2. Configure (add your API keys to .env)
cp .env.example .env
# Edit .env with your Twitter + Anthropic keys

# 3. Run!
python ai_agent.py
```

---

## How It Works

### The Smart Way 🤖

Your bot uses **Claude AI** to:
1. Check for completed NBA games
2. Analyze which games are interesting
3. **Generate custom, creative tweets** (not rigid templates!)
4. Post the best games to Twitter
5. Remember what it posted (no duplicates)

### Example Tweet Flow

```
Game: DET 112 @ MIA 118
Stats: Cade Cunningham 31/8/11 (double-double)
      Norman Powell 36 points

❌ OLD WAY (Rigid):
"🏀 FINAL: MIA 118, DET 112
MIA: Norman Powell
36pts/2reb/2ast"

✅ NEW WAY (Claude's Creativity):
"Cade Cunningham put on a SHOW 🔥 31pts/8reb/11ast 
but Norman Powell's 36 wasn't enough as Miami edges 
Detroit 118-112. What a game! 🏀"
```

---

## Installation

### 1. Prerequisites

- Python 3.8+ 
- Twitter API access (Read + Write permissions)
- Anthropic API key

### 2. Install Dependencies

```bash
cd /Users/jacobtie-shue/Desktop/Projects/nba-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
pip install anthropic
```

### 3. Get API Keys

#### Twitter API

1. Go to https://developer.twitter.com/
2. Create a new App with **Read and Write** permissions
3. Get these credentials:
   - API Key
   - API Key Secret
   - Access Token
   - Access Token Secret  
   - Bearer Token

#### Anthropic API

1. Go to https://console.anthropic.com/
2. Create an API key
3. Copy it (starts with `sk-ant-...`)

---

## Configuration

### Create `.env` File

```bash
cp .env.example .env
```

### Edit `.env` with Your Keys

```env
# ============================================
# REQUIRED: Twitter API Credentials
# ============================================
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

# ============================================
# REQUIRED: Anthropic API (for AI agent)
# ============================================
ANTHROPIC_API_KEY=sk-ant-your_key_here

# ============================================
# CONFIGURATION
# ============================================
ENABLE_BOX_SCORE_POSTING=true
ENABLE_TWEET_MONITORING=false
BOX_SCORE_POST_INTERVAL=1
DATABASE_URL=sqlite:///nba_agent.db
LOG_LEVEL=INFO
```

---

## Running the Agent

The agent can monitor **box scores** or **injury tweets** (or both in separate terminals).

### Option 1: Run Once (Manual)

Check for games and post, then exit:

```bash
python ai_agent.py
```

**Use case:** Run manually when you know games finished.

### Option 2: Continuous Loop (Autonomous)

Keep running, check every N minutes:

```bash
# Check every 5 minutes (default)
python ai_agent.py loop

# Check every 1 minute
python ai_agent.py loop 1

# Check every 30 minutes
python ai_agent.py loop 30
```

**Use case:** Leave running in terminal, fully autonomous.

### Option 3: Interactive Chat

Chat with Claude about NBA games:

```bash
python ai_agent.py interactive
```

**Example conversation:**
```
💬 You: Are there any completed games?

🤖 Agent: Yes! I found 2 completed games:
- HOU 120 @ BKN 96
- MIA 118 @ DET 112

💬 You: Post the interesting one with a creative tweet

🤖 Agent: I'll post the DET/MIA game - Cade had a double-double...
[Generates creative tweet and posts]
Done! Tweet ID: 2006933155236762095
```

---

## Making It Autonomous

### Method 1: Background Loop (Easiest)

Just use the built-in loop mode:

```bash
# Run in background
nohup python ai_agent.py loop 5 > agent.log 2>&1 &

# Check if it's running
ps aux | grep ai_agent

# Stop it
pkill -f ai_agent
```

### Method 2: Cron Job (Recommended)

Run every N minutes automatically:

```bash
# Edit crontab
crontab -e

# Add one of these lines:

# Every 5 minutes
*/5 * * * * cd /Users/jacobtie-shue/Desktop/Projects/nba-agent && /Users/jacobtie-shue/Desktop/Projects/nba-agent/venv/bin/python ai_agent.py >> logs/cron.log 2>&1

# Every hour
0 * * * * cd /Users/jacobtie-shue/Desktop/Projects/nba-agent && /Users/jacobtie-shue/Desktop/Projects/nba-agent/venv/bin/python ai_agent.py >> logs/cron.log 2>&1

# Only during game times (7pm-11pm ET, every 5 min)
*/5 19-23 * * * cd /Users/jacobtie-shue/Desktop/Projects/nba-agent && /Users/jacobtie-shue/Desktop/Projects/nba-agent/venv/bin/python ai_agent.py >> logs/cron.log 2>&1
```

**View cron logs:**
```bash
tail -f logs/cron.log
```

### Method 3: Systemd Service (Production)

**Create service file:**

```bash
sudo nano /etc/systemd/system/nba-agent.service
```

```ini
[Unit]
Description=NBA AI Agent
After=network.target

[Service]
Type=simple
User=jacobtie-shue
WorkingDirectory=/Users/jacobtie-shue/Desktop/Projects/nba-agent
Environment="PATH=/Users/jacobtie-shue/Desktop/Projects/nba-agent/venv/bin"
ExecStart=/Users/jacobtie-shue/Desktop/Projects/nba-agent/venv/bin/python ai_agent.py loop 5
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable nba-agent
sudo systemctl start nba-agent
sudo systemctl status nba-agent

# View logs
journalctl -u nba-agent -f
```

---

## Features

### 🎨 Creative Tweet Generation

Claude generates **unique, contextual tweets** for each game:

- Detects triple-doubles, double-doubles, 30+ point games
- Recognizes close games, upsets, dominant performances
- Uses emojis and dynamic language
- Stays under 280 characters
- **No rigid templates - every tweet is custom!**

### 🚫 Duplicate Prevention

- SQLite database tracks all posted games
- Won't post the same game twice
- Even if you restart the agent

### 📊 Smart Game Selection

Claude decides what's interesting:
- ✅ Triple-doubles and double-doubles
- ✅ 30+ point performances
- ✅ Close games (within 5 points)
- ✅ Surprising upsets
- ❌ Boring blowouts (usually skipped)

### 🔄 Autonomous Operation

- Loop mode: Runs continuously
- Cron job: Scheduled checks
- Systemd: Production-grade service

---

## How the New Smart Tweets Work

### Old Way (Rigid Templates)

```python
# Fixed format in code
tweet = f"🏀 FINAL: {away} {away_score}, {home} {home_score}\n\n"
tweet += f"{team}: {player}\n{pts}pts/{reb}reb/{ast}ast"
```

Every tweet looked the same. Boring!

### New Way (Claude's Creativity)

```python
# Claude sees game stats and crafts unique tweets
tools:
  - generate_custom_tweet(game_id)  # Get stats
  - post_custom_tweet(game_id, creative_text)  # Claude writes it!
```

Claude analyzes the game and writes engaging content that matches what happened.

### Example Outputs

**Triple-Double:**
```
Cade Cunningham MASTERCLASS 🔥 31/8/11 triple-double 
powers Detroit past Miami 112-118. This man is ELITE!
```

**Close Game:**
```
THRILLER in Miami! Norman Powell drops 36 but Cade's 
31/8/11 💪 leads DET to a 112-118 nail-biter. What a finish!
```

**Blowout:**
```
Houston DOMINATES Brooklyn 120-96. Amen Thompson (23/4/3) 
led the charge in a statement win 💪
```

---

## Testing with Dummy Data

Want to test without waiting for real games or tweets? Use test mode!

### Test Box Scores

```bash
# Run with test game data (2 dummy games included)
python ai_agent.py test

# Or use --test flag
python ai_agent.py --test

# Loop mode with test data
python ai_agent.py loop 1 --test
```

**Test data includes:**
- LAL @ BOS: LeBron triple-double (32/12/11)
- GSW @ PHX: Curry 42 points, Booker double-double

### Test Injury Monitoring

```bash
# Run with test injury data (6 dummy tweets included)
python ai_agent.py test injury

# Or use flags
python ai_agent.py --test --injury

# Loop mode with test injury data
python ai_agent.py loop 1 --test --injury
```

**Test injury data includes:**
- LeBron James - ankle sprain, out 2-3 weeks
- Stephen Curry - shoulder soreness, questionable
- Giannis - knee issue, MRI pending
- Deandre Ayton - thumb surgery, out 4-6 weeks
- Joel Embiid - returning from injury
- Trade news (tests filtering)

See `TESTING.md` for full testing guide!

---

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

```bash
# Make sure it's in .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Or export it
export ANTHROPIC_API_KEY=sk-ant-...
```

### "Twitter 403 Forbidden"

Your Access Token doesn't have write permissions:
1. Go to Developer Portal → Your App → "Keys and tokens"
2. **Regenerate** Access Token and Secret
3. Update `.env` with new values

### "Twitter 403 Duplicate Content"

Game was already posted (Twitter blocks exact duplicates):
- Check database: `sqlite3 nba_agent.db "SELECT * FROM box_score_posts;"`
- This is expected - Claude will skip it automatically

### "Model claude-3-5-sonnet-20241022 not found"

Model name changed. Update to:
```python
model="claude-sonnet-4-20250514"
```

(This is already fixed in the current version)

### "No completed games found"

This is normal! Means no NBA games have finished yet. Agent will check again later.

### Cron Job Not Working

```bash
# Check cron is running
sudo systemctl status cron  # Linux
# or check System Preferences → Users → Login Items on macOS

# Test your command manually first
cd /Users/jacobtie-shue/Desktop/Projects/nba-agent
source venv/bin/activate
python ai_agent.py

# Check cron logs
tail -f /var/log/syslog | grep CRON  # Linux
```

---

## Cost Estimate

### Anthropic API

- **Input**: $3 per million tokens (~$0.003 per 1000 tokens)
- **Output**: $15 per million tokens (~$0.015 per 1000 tokens)

**Typical cost per run:** ~$0.01-0.02

**Monthly cost (checking every 5 minutes):**
- ~8,640 checks/month
- Assuming 10% actually post: ~860 posts
- **Total: ~$9-17/month**

Way cheaper than you'd think!

### Twitter API

Free (within rate limits).

---

## Files Overview

| File | Purpose |
|------|---------|
| `ai_agent.py` | **Main AI agent** - Run this! |
| `mcp_server.py` | MCP server (exposes tools to Claude) |
| `manual_main.py` | Simple non-AI automation |
| `test_boxscore.py` | Manual testing script |
| `mcp_client.py` | Test MCP server |
| `nba_agent.db` | SQLite database (auto-created) |
| `.env` | Your API keys (DON'T commit!) |
| `SETUP.md` | **This file** |
| `ARCHITECTURE.md` | Technical deep dive |

---

## Quick Reference

### Common Commands

```bash
# Run once
python ai_agent.py

# Run continuously (check every 5 min)
python ai_agent.py loop 5

# Interactive mode
python ai_agent.py interactive

# Test MCP server
python mcp_client.py

# Check database
sqlite3 nba_agent.db "SELECT game_id, tweet_id, posted_at FROM box_score_posts;"

# View logs
tail -f logs/nba_agent_$(date +%Y-%m-%d).log
```

### Environment Variables

```bash
# Load environment
source venv/bin/activate

# Set API key temporarily
export ANTHROPIC_API_KEY=sk-ant-...

# Check what's loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY')[:20])"
```

---

## What's Next?

### Ideas for Enhancement

1. **Add player injury monitoring** (enable ENABLE_TWEET_MONITORING)
2. **Post highlights** (integrate with video APIs)
3. **Betting insights** (analyze lines and odds)
4. **Thread games** (post live updates during games)
5. **Multi-platform** (cross-post to Bluesky, Mastodon)

### Contributing

The architecture is modular - easy to extend:
- Add tools to `mcp_server.py`
- Update prompts in `ai_agent.py`
- Create new formatters in `analyzers/`

---

## Support

**Issues?** Check:
1. This guide (SETUP.md)
2. Architecture docs (ARCHITECTURE.md)
3. Logs in `logs/` directory
4. Database: `sqlite3 nba_agent.db`

**Still stuck?** The code is well-documented - read through `ai_agent.py` and `mcp_server.py`.

---

## Summary

You now have a **truly autonomous AI NBA bot** that:
- ✅ Checks for games automatically
- ✅ Generates creative, unique tweets
- ✅ Posts interesting games only
- ✅ Runs 24/7 with cron/systemd
- ✅ Costs ~$10/month

**To make it fully autonomous:**
```bash
python ai_agent.py loop 5
```

Or set up a cron job and forget about it! 🚀🏀

---

**Last Updated:** 2026-01-03  
**Agent Version:** 2.0 (Smart Tweets Edition)

