# NBA Box Score Bot - Simple Setup

This is a simplified guide for just posting NBA box scores to Twitter. The tweet monitoring feature is disabled by default (you can enable it later if you want).

## What You Need

1. **Python 3.8+** (check with `python3 --version`)
2. **Twitter API Access** (the only API you need!)

## Step 1: Get Twitter API Credentials

1. Go to https://developer.twitter.com/
2. Sign in and create a new Project/App
3. Set permissions to **Read and Write**
4. Generate these credentials:
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret
   - Bearer Token

Save these somewhere safe!

## Step 2: Install the Bot

```bash
# Navigate to the project
cd /Users/jacobtie-shue/Desktop/Projects/nba-agent

# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Your Bot

Create a `.env` file:

```bash
# Copy the example
cp .env.example .env
```

Now edit `.env` and add your Twitter credentials:

```env
# Twitter API Credentials
TWITTER_API_KEY=paste_your_api_key_here
TWITTER_API_SECRET=paste_your_api_secret_here
TWITTER_ACCESS_TOKEN=paste_your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=paste_your_access_token_secret_here
TWITTER_BEARER_TOKEN=paste_your_bearer_token_here

# Feature Flags (box scores enabled, tweet monitoring disabled)
ENABLE_BOX_SCORE_POSTING=true
ENABLE_TWEET_MONITORING=false

# How often to check for completed games (in minutes)
BOX_SCORE_POST_INTERVAL=60

# Database (SQLite - no setup needed)
DATABASE_URL=sqlite:///nba_agent.db

# Logging
LOG_LEVEL=INFO
```

**That's it!** You don't need an OpenAI API key for just posting box scores.

## Step 4: Run the Bot

```bash
python main.py
```

You should see:

```
============================================================
NBA Agent Starting Up
============================================================
2026-01-01 12:00:00 | INFO     | Validating configuration...
2026-01-01 12:00:00 | INFO     | ✓ Configuration valid
2026-01-01 12:00:00 | INFO     | Initializing database...
2026-01-01 12:00:00 | INFO     | ✓ Database initialized
2026-01-01 12:00:00 | INFO     | Initializing API clients...
2026-01-01 12:00:00 | INFO     | ✓ API clients initialized
2026-01-01 12:00:00 | INFO     | Initializing agents...
2026-01-01 12:00:00 | INFO     |   - Tweet monitoring is DISABLED
2026-01-01 12:00:00 | INFO     |   - Box score posting is ENABLED
2026-01-01 12:00:00 | INFO     | ✓ Agents initialized
2026-01-01 12:00:00 | INFO     | Initializing scheduler...
2026-01-01 12:00:00 | INFO     | Scheduled jobs: box scores every 60 min
2026-01-01 12:00:00 | INFO     | ✓ Scheduler initialized
============================================================
NBA Agent is now running!
Box score posts: every 60 minutes
Press Ctrl+C to stop
============================================================
```

## What It Does

The bot will:
- ✅ Check for completed NBA games every 60 minutes
- ✅ Fetch game scores and top performer stats from the NBA API
- ✅ Post formatted tweets like this:

```
🏀 FINAL: LAL 115, BOS 108

⭐ Top Performers:

LAL: LeBron James
  28pts, 8reb, 11ast

BOS: Jayson Tatum
  32pts, 7reb, 4ast
```

- ✅ Keep track of posted games to avoid duplicates
- ✅ Log everything to `logs/` directory

## Customization

### Change Posting Frequency

Edit `.env`:
```env
BOX_SCORE_POST_INTERVAL=30  # Check every 30 minutes instead
```

### Customize Tweet Format

Edit `analyzers/box_score_formatter.py` to change how tweets look.

### Test Manually

Want to test without waiting? Create a test script:

```python
# test_boxscore.py
from clients import TwitterClient, NBAClient
from analyzers import BoxScoreFormatter

twitter = TwitterClient()
nba = NBAClient()
formatter = BoxScoreFormatter()

# Get today's completed games
games = nba.get_completed_games_today()

print(f"Found {len(games)} completed games:\n")

for game in games:
    # Format the tweet
    tweet_text = formatter.format_game_summary(game)
    print(tweet_text)
    print("-" * 60)
    
    # Uncomment to actually post:
    # tweet_id = twitter.post_tweet(tweet_text)
    # print(f"Posted as tweet {tweet_id}\n")
```

Run it:
```bash
python test_boxscore.py
```

## Troubleshooting

### "Missing required environment variables"
- Make sure your `.env` file is in the project root
- Check that all Twitter credentials are filled in (no quotes needed)

### "Twitter API authentication failed"
- Double-check your credentials are correct
- Ensure your app has Read and Write permissions
- Try regenerating your access token

### "No completed games found"
- This is normal if no games have finished yet
- Games are only posted after they're marked as "Final" by the NBA API
- The bot will keep checking every 60 minutes

### Database errors
- The SQLite database is created automatically
- If you see errors, try deleting `nba_agent.db` and restarting

## Running 24/7

### On Your Computer

Just leave the terminal open! The bot will keep running.

### On a Server (Recommended)

For 24/7 operation, run on a cloud server:

1. **DigitalOcean/Linode** ($5/month)
2. **AWS EC2** (Free tier available)
3. **Google Cloud Compute** (Free tier available)

See the full README.md for deployment instructions.

## Want to Enable Tweet Monitoring Later?

When you're ready to add the Shams injury monitoring feature:

1. Get an OpenAI API key from https://platform.openai.com/
2. Install OpenAI package: `pip install openai>=1.12.0`
3. Edit `.env`:
   ```env
   ENABLE_TWEET_MONITORING=true
   OPENAI_API_KEY=your_openai_key_here
   SHAMS_TWITTER_USERNAME=ShamsCharania
   TWEET_CHECK_INTERVAL=5
   ```
4. Restart the bot

The tweet monitoring code is already there, just disabled!

## Support

- Full documentation: See `README.md`
- Architecture details: See `ARCHITECTURE.md`
- Issues? Check the `logs/` directory for error details

---

That's it! Simple box score posting with just Twitter API credentials. 🏀

