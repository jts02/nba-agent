# 🏀🔥 Smart Heat Bot - Intelligent Miami Heat Twitter Bot

## Overview

The **Smart Heat Bot** is a completely redesigned, intelligent Twitter bot for Miami Heat content. Unlike the previous agents that were surface-level, this bot has:

- **Memory**: Continuously monitors Heat Twitter accounts to learn tone, style, and what gets engagement
- **Context Awareness**: Tracks ongoing narratives (player performances, trade rumors, winning streaks)
- **Knowledge Base**: Stores facts about players, team history, and Heat culture
- **Authentic Personality**: Mix of smart basketball analysis and chaotic humor
- **Multiple Tweet Types**: Live game reactions, Heat discourse replies, original takes, nostalgic throwbacks

## Key Features

### 🧠 Memory System
- Monitors Heat beat reporters, influencers, and official accounts
- Stores tweets with engagement metrics (likes, RTs, replies)
- Learns what content resonates with Heat fans
- Tracks successful tweet patterns and styles

### 📊 Narrative Tracking
- Identifies and tracks ongoing storylines:
  - Player performance trends (hot streaks, slumps)
  - Team dynamics (winning/losing streaks, chemistry)
  - Trade rumors and injury news
  - Playoff implications
  - Rivalries and matchups

### 📚 Knowledge Base
- Stores facts about:
  - Current players (stats, contracts, playing styles)
  - Team history (championships, legendary moments)
  - Heat culture references ("Heat Lifer", Pat Riley lore)
  - Inside jokes and Heat Twitter culture
  - Opponent info for rivalry context

### 🎭 Personality
The bot has a unique dual personality:
- **Smart Analyst**: Breaks down advanced stats, strategy, player development
- **Chaotic Shitposter**: Drops wild takes, salty reactions, nostalgic references

Examples:
- Analytical: "Bam's pick-and-roll defense is elite but his offensive hesitancy in the paint is costing Miami 8-10 possessions per game"
- Chaotic: "Jimmy Butler's coffee addiction is the only consistent thing about this team 💀☕"
- Historical: "2006 Wade >>> your favorite player's best season. That's just facts 👑"

## Files

### Core Files
- `smart_heat_bot.py` - Main agent orchestrator (uses Claude for decision-making)
- `smart_heat_mcp_server.py` - MCP server with all tools (monitoring, context, posting)
- `database/models.py` - Enhanced with new tables for memory system

### Database Tables
- `monitored_tweets` - Tweets scraped from Heat Twitter accounts
- `heat_narratives` - Ongoing storylines and narratives
- `heat_knowledge` - Facts and information about Heat
- `smart_bot_tweets` - Bot's own tweets with performance tracking

## Installation

### 1. Prerequisites
All dependencies are already in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. API Keys
Add to your `.env` file:

```bash
# Required - Claude orchestrates the bot
ANTHROPIC_API_KEY=your_anthropic_key_here

# Required - For posting and monitoring Twitter
TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_secret_here
TWITTER_ACCESS_TOKEN=your_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Database (default is fine)
DATABASE_URL=sqlite:///nba_agent.db
```

### 3. Initialize Database
The bot will automatically create new tables on first run:
```bash
python smart_heat_bot.py --mode monitor
```

## Usage

### Modes

The bot has several modes you can choose:

#### 1. Auto Mode (Recommended)
Bot intelligently decides what to do based on context:
```bash
# Single run - bot decides whether to scrape, analyze, or tweet
python smart_heat_bot.py

# Continuous mode - checks every 15 minutes
python smart_heat_bot.py loop
python smart_heat_bot.py loop 30  # Every 30 minutes
```

The bot will:
- Scrape Heat Twitter to update memory
- Check if there's a live Heat game
- Analyze what Heat Twitter is discussing
- Decide if it should tweet (and what type)
- Only tweet if there's something worth saying

#### 2. Monitor Mode
Just scrape and learn, no tweeting:
```bash
# Build memory without tweeting
python smart_heat_bot.py --mode monitor

# Run continuously to keep memory fresh
python smart_heat_bot.py loop 10 --mode monitor
```

Use this to:
- Build up initial memory before going live
- Keep memory updated without tweeting
- Test scraping functionality

#### 3. Game Mode
Focus on live Heat game reactions:
```bash
# Check once for live game
python smart_heat_bot.py --mode game

# Check every 5 minutes during games
python smart_heat_bot.py loop 5 --mode game
```

The bot will:
- Check if Heat are playing live
- Get box score and game context
- See what Heat Twitter is saying
- Generate smart + chaotic game reaction
- Post tweet if something interesting is happening

#### 4. Discourse Mode
Jump into Heat Twitter discussions:
```bash
# Reply to trending Heat topics
python smart_heat_bot.py --mode discourse

# Check every 20 minutes for hot topics
python smart_heat_bot.py loop 20 --mode discourse
```

The bot will:
- Scrape recent Heat Twitter
- Identify trending topics/debates
- Get relevant narratives and context
- Generate an engaging tweet that adds to discourse
- Post it

#### 5. Original Mode
Drop standalone Heat takes:
```bash
# Post an original take
python smart_heat_bot.py --mode original

# Post original takes every 30 minutes
python smart_heat_bot.py loop 30 --mode original
```

The bot will:
- Pull from knowledge base and narratives
- Check what it tweeted recently (avoid repetition)
- Generate original take (analytical, nostalgic, controversial, or chaotic)
- Post it

## Monitored Accounts

The bot learns from these Heat Twitter accounts (configured in `smart_heat_mcp_server.py`):

### Beat Reporters
- @IraHeatBeat (Ira Winderman - Sun Sentinel)
- @Anthony_Chiang (Miami Herald)
- @AhnFireDigital (Heat insider)

### Heat Influencers/Fan Accounts
- @5ReasonsSports (Popular Heat content)
- @HeatVsHaters (Passionate Heat fan account)
- @MiamiHeatBeat (Heat analysis)

### Official Accounts
- @MiamiHEAT (Official team account)

### NBA News (for context)
- @ShamsCharania (Shams Charania)
- @wojespn (Adrian Wojnarowski)
- @TheSteinLine (Marc Stein)

**Note**: Player accounts are NOT monitored (players change teams). Only team, reporters, influencers, and news sources.

You can modify these in `smart_heat_mcp_server.py` in the `HEAT_ACCOUNTS` dictionary.

## Example Workflows

### Initial Setup (First Time)
```bash
# 1. Build initial memory (run for a few hours)
python smart_heat_bot.py loop 10 --mode monitor

# 2. Once memory is built, switch to auto mode
python smart_heat_bot.py loop 20
```

### During Heat Game
```bash
# Check every 5 minutes for game reactions
python smart_heat_bot.py loop 5 --mode game
```

### General Daily Operation
```bash
# Auto mode - bot decides when to tweet
python smart_heat_bot.py loop 15
```

### Overnight/Maintenance
```bash
# Just monitor and build memory
python smart_heat_bot.py loop 30 --mode monitor
```

## How the Bot Decides What to Tweet

The bot uses Claude with full context to make intelligent decisions:

1. **Scrape Recent Heat Twitter**: Get last 6-24 hours of tweets from monitored accounts
2. **Analyze Context**: What are people talking about? What's trending?
3. **Check Narratives**: What ongoing storylines are active?
4. **Check Live Game**: Is the Heat playing right now?
5. **Review Recent Bot Tweets**: Did we tweet recently? About what?
6. **Decide**:
   - Live game + interesting moment? → Game reaction tweet
   - Hot Heat Twitter topic? → Jump into discourse
   - Slow day but good opportunity? → Original take
   - Tweeted recently or nothing interesting? → Just monitor

7. **Generate Tweet**: Uses ALL context to craft authentic, engaging tweet
8. **Post & Track**: Posts to Twitter and tracks performance in database

## Tweet Quality Control

The bot is designed to prioritize quality:
- **No spam**: Checks recent tweets to avoid over-posting
- **Context-aware**: Every tweet uses current narratives and Heat Twitter tone
- **Authentic**: Learned from actual Heat Twitter, not generic
- **Engaging**: Mix of analysis and chaos keeps it interesting
- **Performance tracking**: Tracks likes/RTs to learn what works

## Bot Personality Guidelines

The system prompt teaches Claude to be:

### Smart Analyst Side
- Break down advanced stats and strategy
- Reference player development and coaching decisions
- Make bold but informed predictions
- Use basketball IQ to add value

### Chaotic Side
- Drop wild hot takes and controversial opinions
- Reference Heat history and nostalgia
- Use Heat Twitter slang and culture
- Be salty but entertaining

### Balance
- Don't be one-note - mix analytical and chaos
- Keep tweets SHORT and punchy (100-200 chars ideal)
- Use emojis strategically 🔥💀😤👑🏆🤡
- Reference current narratives naturally
- Avoid corporate speak and bland takes

## Advanced Features

### Manual Narrative Management
You can manually add/update narratives:

```python
# Example: Track Bam's shooting slump
python -c "
from database import DatabaseManager
import asyncio
# ... (code to add narrative manually)
"
```

Or use the bot's tools through the MCP server.

### Knowledge Base Management
Add facts manually or let the bot learn from Twitter:

```python
# Example: Add Heat history fact
# Similar to narratives, can be done programmatically
```

### Performance Analysis
Check how bot tweets are performing:

```sql
-- Query the database
SELECT tweet_text, likes, retweets, replies, performance_score
FROM smart_bot_tweets
ORDER BY posted_at DESC
LIMIT 20;
```

## Monitoring and Debugging

### Check Bot Activity
```bash
# See recent bot tweets
sqlite3 nba_agent.db "SELECT posted_at, tweet_type, tweet_text FROM smart_bot_tweets ORDER BY posted_at DESC LIMIT 10;"

# See monitored tweets
sqlite3 nba_agent.db "SELECT author_username, tweet_text, likes FROM monitored_tweets ORDER BY scraped_at DESC LIMIT 10;"

# See active narratives
sqlite3 nba_agent.db "SELECT title, description, status FROM heat_narratives WHERE status='active';"
```

### Logs
The bot outputs detailed logs to console:
- Which tools it's using
- What context it's considering
- Why it decided to tweet (or not)
- What it posted

## Comparison: Smart Heat Bot vs Previous Bots

| Feature | ai_agent.py | heat_fan_agent.py | **Smart Heat Bot** |
|---------|-------------|-------------------|-------------------|
| **Focus** | All NBA teams | Heat live games | Heat everything |
| **Memory** | None | Minimal (snapshots) | **Full Twitter monitoring** |
| **Context** | Basic | Game stats only | **Narratives, knowledge, discourse** |
| **Personality** | Professional | Unhinged fan | **Smart + Chaotic mix** |
| **Tweet Types** | Box scores, injuries | Game reactions | **Game, discourse, original, nostalgia** |
| **Learning** | No | No | **Yes - learns from engagement** |
| **Authenticity** | Generic | Reactive | **Culture-aware, contextual** |

## Troubleshooting

### "No tweets being posted"
- Bot is being selective - this is good!
- Check console logs to see decision-making
- Try `--mode original` to force a tweet
- Make sure memory is built up (run `--mode monitor` first)

### "Twitter API rate limits" ⚠️ COMMON ISSUE
**Problem**: Twitter locks you out for 12-15 minutes when scraping too much.

**How the bot handles it**:
- Saves any tweets it got before the rate limit
- Returns a clear message: "⚠️ RATE LIMITED - Wait 15 minutes"
- Stops trying to scrape more accounts
- Can still tweet using existing database context

**How to avoid rate limits**:
1. **Reduce tweets per account**: Use `max_tweets_per_account=10` instead of 20
   ```python
   # In smart_heat_mcp_server.py, the bot can adjust this
   # Or manually: scrape_heat_twitter(max_tweets_per_account=10)
   ```

2. **Scrape specific categories**: Instead of "all", scrape one category at a time
   ```bash
   # Instead of scraping all at once
   python smart_heat_bot.py --mode monitor  # Scrapes all 10 accounts

   # Do this - scrape beat reporters only
   # (modify bot to use: scrape_heat_twitter(account_category="beat_reporters"))
   ```

3. **Increase time between scrapes**: Use longer intervals
   ```bash
   # More time = less rate limit risk
   python smart_heat_bot.py loop 30 --mode monitor  # Every 30 min instead of 10
   ```

4. **Bot works even when rate limited**: It uses existing database context!
   - The bot has memory from previous scrapes
   - Can still tweet based on narratives and knowledge
   - Just won't have the absolute latest tweets

**If you get rate limited**:
- Wait 15 minutes before trying to scrape again
- The bot will tell you: "Wait 15 minutes before scraping again"
- You can still run in other modes (game, discourse, original) using existing context
- Or just let it rest and come back later

### "Bot tweets are repetitive"
- It should check recent tweets automatically
- May need more varied narratives in knowledge base
- Adjust personality prompt in `smart_heat_bot.py`

### "Not learning Heat Twitter style"
- Run monitor mode longer to build memory
- Check that monitored accounts are correct
- Verify tweets are being scraped (check database)

## Production Recommendations

### Daily Operation
```bash
# Run in auto mode with moderate frequency
python smart_heat_bot.py loop 20
```

### Game Days
```bash
# Terminal 1: Smart bot in auto mode (general coverage)
python smart_heat_bot.py loop 15

# Terminal 2: Game mode during Heat games (frequent reactions)
python smart_heat_bot.py loop 5 --mode game
```

### Overnight
```bash
# Just monitor and build memory
python smart_heat_bot.py loop 60 --mode monitor
```

### Tweet Limits
- Recommended: 10-20 tweets per day max
- Bot naturally spaces tweets out
- Quality over quantity approach

## Future Enhancements

Potential additions:
- Reply detection and conversation threads
- Image/GIF generation for tweets
- Sentiment analysis on monitored tweets
- Auto-update knowledge from game stats
- A/B testing different tweet styles
- Integration with Heat subreddit
- Player mention tracking
- Rival team monitoring for smack talk

## Tips for Best Results

1. **Build Memory First**: Run monitor mode for several hours before going live
2. **Use Auto Mode**: Let Claude decide - it's smart about when to tweet
3. **Monitor Console**: Watch the decision-making process
4. **Adjust Personality**: Edit system prompt in `smart_heat_bot.py` to tune personality
5. **Add Narratives**: Manually add key storylines for better context
6. **Track Performance**: Check database to see what tweets work best
7. **Be Patient**: Quality > quantity approach means fewer but better tweets

## Getting Started Checklist

- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Add API keys to `.env` (Anthropic + Twitter)
- [ ] Run initial memory build: `python smart_heat_bot.py loop 10 --mode monitor`
- [ ] Let it scrape for a few hours
- [ ] Switch to auto mode: `python smart_heat_bot.py loop 20`
- [ ] Monitor console and database for first few tweets
- [ ] Adjust personality if needed
- [ ] Enjoy your smart, authentic Heat Twitter bot! 🔥🏀

---

Built with Claude Sonnet 4.5, MCP, and way too much Heat fandom. 🔥🏆
