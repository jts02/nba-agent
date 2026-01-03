# Injury Monitoring Feature

## Overview

The NBA Agent now monitors Shams Charania's Twitter for injury-related tweets and automatically reposts them!

## How It Works

1. **Fetch Tweets**: Gets recent tweets from @ShamsCharania
2. **AI Analysis**: Uses Claude (Anthropic) to detect injury-related content
3. **Extract Details**: Identifies player name, injury type, and time missed
4. **Auto-Post**: Retweets injury news or posts custom injury reports
5. **Track**: Saves processed tweets to database to avoid duplicates

## Quick Start

### Production Mode (Real Twitter)

```bash
# Run once
python ai_agent.py injury

# Run continuously (every 5 minutes)
python ai_agent.py loop 5 injury
```

**Requirements:**
- `ENABLE_TWEET_MONITORING=true` in `.env`
- `ANTHROPIC_API_KEY` in `.env` (same one you use for the agent)
- Twitter API credentials with read permissions

### Test Mode (Dummy Data)

```bash
# Run once with test data
python ai_agent.py test injury

# Or use flags
python ai_agent.py --test --injury

# Run continuously
python ai_agent.py loop 1 --test --injury
```

**No API keys needed for testing!** Uses keyword matching instead of Claude AI.

## Test Data

Six dummy tweets in `test_injury_data.json`:

1. **LeBron James** - ankle sprain, out 2-3 weeks ✅ Injury
2. **Stephen Curry** - shoulder soreness, questionable ✅ Injury
3. **Giannis Antetokounmpo** - knee issue, MRI pending ✅ Injury
4. **Trade news** - Kyle Lowry trade ❌ Not injury (tests filtering)
5. **Deandre Ayton** - thumb surgery, out 4-6 weeks ✅ Injury
6. **Joel Embiid** - returning from injury ✅ Injury

## MCP Tools Available

When running in injury mode, Claude has access to:

### `get_recent_tweets`
Fetch recent tweets from a Twitter user.

```python
await get_recent_tweets(username="ShamsCharania", max_results=10)
```

### `analyze_tweet_for_injury`
Analyze if a tweet contains injury information.

```python
result = await analyze_tweet_for_injury(tweet_text)
# Returns: {"is_injury": bool, "confidence": float, "summary": str}
```

### `extract_injury_details`
Extract specific injury details from a tweet (test mode only).

```python
details = await extract_injury_details(tweet_text)
# Returns: {"player_name": str, "injury_type": str, "time_missed": str}
```

### `post_injury_tweet`
Post a formatted injury report tweet.

```python
result = await post_injury_tweet(
    player_name="LeBron James",
    injury_type="ankle sprain",
    time_missed="2-3 weeks"
)
```

### `check_and_post_injury_tweets`
All-in-one: check for new tweets, analyze, and post.

```python
result = await check_and_post_injury_tweets(username="ShamsCharania")
# Returns: {"new_tweets": int, "injury_tweets": int, "posted": int}
```

### `get_processed_injury_tweets`
Get all processed injury tweets from database.

```python
tweets = await get_processed_injury_tweets()
```

## Database Schema

Injury tweets are stored in the `processed_tweets` table:

```sql
CREATE TABLE processed_tweets (
    id INTEGER PRIMARY KEY,
    tweet_id VARCHAR(50) UNIQUE NOT NULL,
    author_username VARCHAR(100) NOT NULL,
    tweet_text TEXT NOT NULL,
    is_injury_related BOOLEAN DEFAULT FALSE,
    reposted BOOLEAN DEFAULT FALSE,
    repost_id VARCHAR(50),
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Example Output

### Test Mode

```bash
$ python ai_agent.py test injury

============================================================
🧪 TEST MODE - INJURY MONITORING (Using dummy tweets)
============================================================
✅ API key found
🔌 Connecting to MCP server (TEST)...
✅ Connected to MCP server
✅ Loaded 7 tools

============================================================
🎯 Task: Check for injury tweets
============================================================

🔧 Claude is using tools...
   • Calling: check_and_post_injury_tweets

============================================================
🧪 TEST MODE - Generated Injury Tweet (NOT posted):
============================================================
🏥 Injury Report: LeBron James - ankle injury. Expected to miss 2-3 weeks.
============================================================
Length: 72 characters
============================================================

📝 Claude's Summary:
I found 5 injury-related tweets from Shams Charania:

1. ✅ LeBron James - ankle sprain, out 2-3 weeks
2. ✅ Giannis Antetokounmpo - knee issue, MRI pending
3. ✅ Deandre Ayton - thumb surgery, out 4-6 weeks
4. ❌ Trade news (filtered out)
5. ✅ Joel Embiid - returning from injury

Posted 3 injury reports (skipped return-from-injury and questionable status).
```

## Running Both Modes

You can run box scores and injury monitoring simultaneously:

```bash
# Terminal 1 - Box scores every hour
python ai_agent.py loop 60

# Terminal 2 - Injuries every 5 minutes
python ai_agent.py loop 5 injury
```

## Configuration

Add to `.env`:

```bash
# Enable injury monitoring (production mode)
ENABLE_TWEET_MONITORING=true

# Anthropic API key (for injury detection - same one used for the agent)
ANTHROPIC_API_KEY=sk-ant-...

# Target Twitter account to monitor
SHAMS_TWITTER_USERNAME=ShamsCharania
```

## Troubleshooting

**"Injury detection not enabled"**
- Set `ENABLE_TWEET_MONITORING=true` in `.env`
- Set `ANTHROPIC_API_KEY` in `.env` (same key you use for the agent)
- Restart the agent

**"No new tweets found"**
- Normal! Shams doesn't tweet every minute
- Try test mode to verify the workflow works
- Check Twitter API rate limits

**Test mode not detecting injuries**
- Test mode uses keyword matching (not Claude AI)
- Requires at least 2 injury keywords in tweet
- Keywords: injury, injured, hurt, sprain, strain, tear, surgery, MRI, out, miss, questionable, doubtful
- Production mode uses Claude for better accuracy

## Clean Up Test Data

```bash
# Delete test injury posts from database
sqlite3 nba_agent.db "DELETE FROM processed_tweets WHERE tweet_id LIKE '12345678%';"

# View test posts
sqlite3 nba_agent.db "SELECT tweet_id, author_username, is_injury_related, reposted FROM processed_tweets WHERE tweet_id LIKE '12345678%';"
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI Agent (Claude)                     │
│  - Decides when to check for tweets                      │
│  - Analyzes which injuries are newsworthy                │
│  - Crafts retweets or custom posts                       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              MCP Server (mcp_server.py)                  │
│  - Exposes tools to Claude                               │
│  - get_recent_tweets()                                   │
│  - analyze_tweet_for_injury()                            │
│  - post_injury_tweet()                                   │
│  - check_and_post_injury_tweets()                        │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│  Twitter Client  │  │ Injury Detector  │
│  (tweepy)        │  │  (Claude AI)     │
│                  │  │                  │
│  - Fetch tweets  │  │  - Analyze text  │
│  - Retweet       │  │  - Extract info  │
│  - Post tweet    │  │  - Confidence    │
└──────────────────┘  └──────────────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
        ┌──────────────────────┐
        │  Database (SQLite)    │
        │  - processed_tweets   │
        │  - Avoid duplicates   │
        └──────────────────────┘
```

## Future Enhancements

- [ ] Support multiple Twitter accounts (not just Shams)
- [ ] Custom injury severity thresholds
- [ ] Injury impact analysis (team standings, playoff implications)
- [ ] Player injury history tracking
- [ ] Integration with fantasy basketball APIs
- [ ] Slack/Discord notifications for major injuries

---

**Happy Injury Monitoring!** 🏥🏀

