# NBA Agent 🏀

An intelligent AI agent that automatically monitors NBA news and posts game updates to Twitter.

## Features

- **Injury News Monitoring**: Automatically monitors tweets from Shams Charania for NBA injury news
- **AI-Powered Detection**: Uses OpenAI GPT to intelligently detect injury-related tweets with high accuracy
- **Automatic Reposting**: Reposts injury news with professional commentary
- **Box Score Updates**: Fetches and posts NBA game box scores with top performer stats
- **Smart Scheduling**: Configurable intervals for tweet monitoring and game updates
- **Database Tracking**: Prevents duplicate posts and maintains complete history
- **Robust Error Handling**: Graceful handling of API rate limits and errors

## Architecture

The agent is built with a modular, scalable architecture:

```
nba-agent/
├── agents/              # Agent orchestration layer
│   ├── tweet_monitor.py    # Monitors and processes tweets
│   └── box_score_agent.py  # Posts NBA box scores
├── analyzers/           # AI analysis modules
│   ├── injury_detector.py  # OpenAI-powered injury detection
│   └── box_score_formatter.py  # Tweet formatting utilities
├── clients/             # External API clients
│   ├── twitter_client.py   # Twitter API wrapper
│   └── nba_client.py      # NBA API wrapper
├── config/              # Configuration management
│   └── settings.py        # Environment-based settings
├── database/            # Database models and management
│   └── models.py         # SQLAlchemy models
├── scheduler/           # Job scheduling
│   └── job_scheduler.py  # APScheduler-based scheduler
├── utils/               # Utilities
│   └── logger.py         # Logging configuration
└── main.py              # Application entry point
```

## Prerequisites

- Python 3.8 or higher
- Twitter API access (API Key, Secret, Access Tokens, Bearer Token)
- OpenAI API key
- SQLite (included with Python) or PostgreSQL

## Installation

1. **Clone the repository**:
```bash
cd /Users/jacobtie-shue/Desktop/Projects/nba-agent
```

2. **Create a virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env and add your API credentials
```

## Configuration

Edit the `.env` file with your credentials:

```env
# Twitter API Credentials
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Target Twitter Account (default: Shams Charania)
SHAMS_TWITTER_USERNAME=ShamsCharania

# Scheduling Configuration (in minutes)
TWEET_CHECK_INTERVAL=5        # Check for new tweets every 5 minutes
BOX_SCORE_POST_INTERVAL=60    # Post box scores every 60 minutes

# Database
DATABASE_URL=sqlite:///nba_agent.db

# Logging
LOG_LEVEL=INFO
```

### Getting API Credentials

#### Twitter API
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new project and app
3. Enable OAuth 1.0a with Read and Write permissions
4. Generate API Key, API Secret, Access Token, and Access Token Secret
5. Copy the Bearer Token from the app settings

#### OpenAI API
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

## Usage

### Running the Agent

**Start the agent**:
```bash
python main.py
```

The agent will:
1. Initialize all components (database, API clients, schedulers)
2. Start monitoring for new tweets
3. Check for completed NBA games
4. Run continuously until stopped (Ctrl+C)

### Manual Operations

You can also create custom scripts to run specific operations:

**Check for injury tweets manually**:
```python
from config import settings
from clients import TwitterClient
from analyzers import InjuryDetector
from database import DatabaseManager
from agents import TweetMonitorAgent

# Initialize components
db_manager = DatabaseManager(settings.DATABASE_URL)
db_manager.create_tables()

twitter_client = TwitterClient()
injury_detector = InjuryDetector()

# Create agent
tweet_monitor = TweetMonitorAgent(
    twitter_client=twitter_client,
    injury_detector=injury_detector,
    db_manager=db_manager,
    target_username=settings.SHAMS_TWITTER_USERNAME
)

# Process tweets
tweet_monitor.process_new_tweets()
```

**Post box scores manually**:
```python
from clients import TwitterClient, NBAClient
from database import DatabaseManager
from agents import BoxScoreAgent

# Initialize components
db_manager = DatabaseManager(settings.DATABASE_URL)
twitter_client = TwitterClient()
nba_client = NBAClient()

# Create agent
box_score_agent = BoxScoreAgent(
    twitter_client=twitter_client,
    nba_client=nba_client,
    db_manager=db_manager
)

# Post recent box scores
box_score_agent.post_recent_box_scores()
```

## Database Schema

### ProcessedTweet
Tracks all processed tweets to avoid duplicates:
- `tweet_id`: Unique tweet identifier
- `author_username`: Tweet author
- `tweet_text`: Original tweet content
- `is_injury_related`: AI detection result
- `reposted`: Whether the tweet was reposted
- `processed_at`: Processing timestamp

### BoxScorePost
Tracks all posted box scores:
- `game_id`: NBA game identifier
- `game_date`: Game date
- `home_team` / `away_team`: Team abbreviations
- `home_score` / `away_score`: Final scores
- `post_text`: Posted tweet content
- `tweet_id`: Posted tweet ID
- `posted_at`: Posting timestamp

### AgentLog
System logs for monitoring:
- `timestamp`: Log timestamp
- `log_level`: Log severity
- `component`: Component name
- `message`: Log message
- `error_details`: Error stack trace (if applicable)

## Monitoring & Logs

Logs are stored in two places:
1. **Console output**: Real-time colored logs
2. **Log files**: `logs/nba_agent_YYYY-MM-DD.log`

Logs rotate daily and are kept for 30 days. Old logs are automatically compressed.

## Customization

### Change Monitored Twitter Account

Edit `.env`:
```env
SHAMS_TWITTER_USERNAME=AnotherReporter
```

### Adjust Scheduling Intervals

Edit `.env`:
```env
TWEET_CHECK_INTERVAL=3      # Check every 3 minutes
BOX_SCORE_POST_INTERVAL=30  # Post every 30 minutes
```

### Customize Tweet Formatting

Edit `analyzers/box_score_formatter.py` to modify how box scores are formatted.

### Adjust Injury Detection Sensitivity

Edit `analyzers/injury_detector.py` to modify the AI prompt or confidence threshold.

## Error Handling

The agent includes robust error handling:
- **API Rate Limits**: Automatically waits when rate limited
- **Network Errors**: Logs errors and continues operation
- **Database Errors**: Rolls back transactions on failure
- **Graceful Shutdown**: Handles SIGINT/SIGTERM signals properly

## Development

### Project Structure Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Components receive dependencies explicitly
3. **Database Sessions**: Proper session management with rollback on errors
4. **Logging**: Comprehensive logging at all levels
5. **Configuration**: Environment-based configuration

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests (when implemented)
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Troubleshooting

### "Missing required environment variables"
- Ensure all required variables are set in `.env`
- Check that `.env` file is in the project root directory

### "Twitter API authentication failed"
- Verify your Twitter API credentials are correct
- Ensure your app has Read and Write permissions
- Check that your Bearer Token is valid

### "OpenAI API error"
- Verify your OpenAI API key is correct
- Check your OpenAI account has available credits
- Ensure you have access to the GPT-4o-mini model

### "No tweets found"
- The target user may not have posted new tweets
- Check the username is correct
- Verify your Twitter API access level

### Database locked errors
- If using SQLite, ensure only one instance is running
- Consider using PostgreSQL for production

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/nba-agent.service`:

```ini
[Unit]
Description=NBA Agent
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/nba-agent
Environment=PATH=/path/to/nba-agent/venv/bin
ExecStart=/path/to/nba-agent/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable nba-agent
sudo systemctl start nba-agent
sudo systemctl status nba-agent
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t nba-agent .
docker run -d --name nba-agent --env-file .env nba-agent
```

## License

MIT License - feel free to use and modify as needed.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Note**: This agent is for educational purposes. Please respect Twitter's API terms of service and rate limits. Always ensure you have the right to repost content.

