# NBA Agent - Quick Start Guide

Get your NBA Agent up and running in 5 minutes!

## Step 1: Install Python Dependencies

```bash
# Make sure you're in the project directory
cd /Users/jacobtie-shue/Desktop/Projects/nba-agent

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Get Your API Keys

### Twitter API (Required)

1. Go to https://developer.twitter.com/
2. Create a new App
3. Navigate to "Keys and tokens"
4. Generate:
   - API Key and Secret
   - Access Token and Secret
   - Bearer Token

### OpenAI API (Required)

1. Go to https://platform.openai.com/
2. Navigate to API Keys
3. Create a new key
4. Copy the key (you'll only see it once!)

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example
cat > .env << 'EOF'
# Twitter API Credentials
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Target Twitter Account
SHAMS_TWITTER_USERNAME=ShamsCharania

# Scheduling (in minutes)
TWEET_CHECK_INTERVAL=5
BOX_SCORE_POST_INTERVAL=60

# Database
DATABASE_URL=sqlite:///nba_agent.db

# Logging
LOG_LEVEL=INFO
EOF
```

Now edit the `.env` file and replace the placeholder values with your actual API keys.

## Step 4: Run the Agent

```bash
python main.py
```

You should see output like:

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
2026-01-01 12:00:00 | INFO     | Initializing AI analyzers...
2026-01-01 12:00:00 | INFO     | ✓ AI analyzers initialized
2026-01-01 12:00:00 | INFO     | Initializing agents...
2026-01-01 12:00:00 | INFO     | ✓ Agents initialized
2026-01-01 12:00:00 | INFO     | Initializing scheduler...
2026-01-01 12:00:00 | INFO     | ✓ Scheduler initialized
============================================================
NBA Agent Setup Complete
============================================================
2026-01-01 12:00:00 | INFO     | NBA Agent is now running!
2026-01-01 12:00:00 | INFO     | Monitoring: @ShamsCharania
2026-01-01 12:00:00 | INFO     | Tweet checks: every 5 minutes
2026-01-01 12:00:00 | INFO     | Box score posts: every 60 minutes
2026-01-01 12:00:00 | INFO     | Press Ctrl+C to stop
============================================================
```

## Step 5: Monitor the Agent

The agent will now:
- ✅ Check for new tweets from Shams Charania every 5 minutes
- ✅ Analyze tweets for injury news using AI
- ✅ Automatically repost injury-related tweets
- ✅ Post NBA box scores every 60 minutes
- ✅ Keep track of everything in the database

### View Logs

Logs are saved in `logs/` directory:

```bash
# View today's log
tail -f logs/nba_agent_$(date +%Y-%m-%d).log

# View recent activity
tail -n 100 logs/nba_agent_$(date +%Y-%m-%d).log
```

### Check Database

```bash
# Install SQLite browser (optional)
brew install sqlite  # macOS
apt install sqlite3  # Linux

# View processed tweets
sqlite3 nba_agent.db "SELECT * FROM processed_tweets ORDER BY processed_at DESC LIMIT 10;"

# View posted box scores
sqlite3 nba_agent.db "SELECT * FROM box_score_posts ORDER BY posted_at DESC LIMIT 10;"
```

## Troubleshooting

### Error: "Missing required environment variables"

**Solution**: Check that all required variables are set in your `.env` file:
```bash
# Check your .env file
cat .env

# Make sure it's in the project root
ls -la .env
```

### Error: "Twitter API authentication failed"

**Solutions**:
1. Verify your Twitter API credentials are correct
2. Check that your app has Read and Write permissions
3. Make sure you copied the entire token (no spaces)
4. Try regenerating your tokens

### Error: "OpenAI API error"

**Solutions**:
1. Verify your OpenAI API key is correct
2. Check your account has credits: https://platform.openai.com/account/usage
3. Ensure you have access to GPT-4o-mini model

### No tweets being found

**Possible reasons**:
1. The target user hasn't posted recently
2. You've already processed all recent tweets
3. Check the username is correct in your `.env` file

## Customization

### Monitor a Different Reporter

Edit `.env`:
```env
SHAMS_TWITTER_USERNAME=wojespn  # Adrian Wojnarowski
```

### Change Check Frequency

Edit `.env`:
```env
TWEET_CHECK_INTERVAL=2      # Check every 2 minutes (more frequent)
BOX_SCORE_POST_INTERVAL=30  # Post scores every 30 minutes
```

### Adjust AI Sensitivity

Edit `analyzers/injury_detector.py` and change the confidence threshold:

```python
# Current: only repost if confidence >= 0.7
if is_injury and confidence >= 0.7:

# More sensitive: repost if confidence >= 0.5
if is_injury and confidence >= 0.5:

# Less sensitive: repost if confidence >= 0.9
if is_injury and confidence >= 0.9:
```

## Testing

### Test Tweet Monitoring

```python
# Create test.py
from config import settings
from clients import TwitterClient
from analyzers import InjuryDetector

twitter = TwitterClient()
detector = InjuryDetector()

# Fetch recent tweets
tweets = twitter.get_user_recent_tweets("ShamsCharania", max_results=5)

# Analyze each one
for tweet in tweets:
    result = detector.is_injury_related(tweet['text'])
    print(f"\nTweet: {tweet['text'][:100]}...")
    print(f"Injury: {result['is_injury']}, Confidence: {result['confidence']}")
    print(f"Summary: {result['summary']}")
```

Run it:
```bash
python test.py
```

### Test Box Score Posting

```python
# Create test_boxscore.py
from clients import NBAClient
from analyzers import BoxScoreFormatter

nba = NBAClient()
formatter = BoxScoreFormatter()

# Get today's completed games
games = nba.get_completed_games_today()

# Format each one
for game in games:
    tweet = formatter.format_game_summary(game)
    print(f"\n{tweet}\n")
    print("-" * 60)
```

Run it:
```bash
python test_boxscore.py
```

## Stopping the Agent

Press `Ctrl+C` in the terminal where the agent is running:

```
^C
2026-01-01 14:30:00 | INFO     | Received keyboard interrupt
============================================================
NBA Agent Shutting Down
============================================================
2026-01-01 14:30:00 | INFO     | Scheduler stopped
2026-01-01 14:30:00 | INFO     | NBA Agent stopped successfully
============================================================
```

## Next Steps

- Read `README.md` for detailed documentation
- Review `ARCHITECTURE.md` to understand the system design
- Customize the agent for your specific needs
- Deploy to a server for 24/7 operation

## Production Deployment

For 24/7 operation, deploy to a server:

### Option 1: Linux Server with systemd

1. Copy files to server
2. Install dependencies
3. Create systemd service (see README.md)
4. Enable and start service

### Option 2: Docker

1. Build Docker image
2. Run container with environment variables
3. Use Docker Compose for easier management

### Option 3: Cloud Platform

- **AWS**: EC2 + RDS
- **Google Cloud**: Compute Engine + Cloud SQL
- **Heroku**: Easy deployment with addons

See README.md for detailed deployment instructions.

## Support

Need help? Check:
1. README.md - Comprehensive documentation
2. ARCHITECTURE.md - Technical details
3. Logs in `logs/` directory
4. GitHub Issues (if applicable)

---

Happy automating! 🏀🤖

