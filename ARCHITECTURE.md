# NBA Agent - Architecture Documentation

## Overview

The NBA Agent is designed with a modular, event-driven architecture that separates concerns and enables scalability. The system consists of several key layers:

1. **Configuration Layer**: Manages application settings and environment variables
2. **Data Layer**: Handles database operations and persistence
3. **Client Layer**: Interfaces with external APIs (Twitter, NBA, OpenAI)
4. **Analysis Layer**: AI-powered content analysis and formatting
5. **Agent Layer**: Business logic orchestration
6. **Scheduler Layer**: Periodic task execution
7. **Application Layer**: Main entry point and lifecycle management

## Component Details

### 1. Configuration Layer (`config/`)

**Purpose**: Centralize configuration management and environment validation.

**Components**:
- `settings.py`: Loads and validates environment variables
  - Twitter API credentials
  - OpenAI API key
  - Scheduling intervals
  - Database connection string
  - Logging configuration

**Design Decisions**:
- Use environment variables for sensitive data (12-factor app methodology)
- Fail fast with validation on startup
- Provide sensible defaults for non-sensitive settings

### 2. Data Layer (`database/`)

**Purpose**: Manage data persistence and prevent duplicate operations.

**Components**:
- `models.py`: SQLAlchemy ORM models
  - `ProcessedTweet`: Tracks processed tweets to avoid reposting
  - `BoxScorePost`: Tracks posted box scores to prevent duplicates
  - `AgentLog`: Application logs for monitoring
  - `DatabaseManager`: Connection and session management

**Design Decisions**:
- Use SQLAlchemy ORM for database abstraction
- Support both SQLite (development) and PostgreSQL (production)
- Index frequently queried fields (tweet_id, game_id)
- Proper session management with rollback on errors

**Database Schema**:

```
ProcessedTweet
├── id (PK)
├── tweet_id (UNIQUE, INDEXED)
├── author_username
├── tweet_text
├── is_injury_related
├── reposted
├── repost_id
└── processed_at

BoxScorePost
├── id (PK)
├── game_id (UNIQUE, INDEXED)
├── game_date
├── home_team
├── away_team
├── home_score
├── away_score
├── post_text
├── tweet_id
└── posted_at

AgentLog
├── id (PK)
├── timestamp (INDEXED)
├── log_level
├── component
├── message
└── error_details
```

### 3. Client Layer (`clients/`)

**Purpose**: Encapsulate external API interactions and handle rate limiting.

#### TwitterClient (`twitter_client.py`)

**Responsibilities**:
- Fetch recent tweets from specific users
- Post new tweets
- Retweet existing tweets
- Quote tweet with commentary
- Handle Twitter API rate limits

**Key Methods**:
- `get_user_recent_tweets()`: Fetch tweets with pagination support
- `retweet()`: Retweet by ID
- `quote_tweet()`: Add commentary to retweet
- `post_tweet()`: Create new tweet

**Design Decisions**:
- Use tweepy library for Twitter API v2
- Enable automatic rate limit handling (`wait_on_rate_limit=True`)
- Return structured dictionaries for consistency
- Log all API operations

#### NBAClient (`nba_client.py`)

**Responsibilities**:
- Fetch game schedules and scores
- Retrieve detailed box scores
- Extract top performers
- Convert team IDs to names/abbreviations

**Key Methods**:
- `get_completed_games_today()`: Fetch finished games
- `get_box_score()`: Get detailed stats for a game
- `get_top_performers()`: Extract leading scorers/performers

**Design Decisions**:
- Use nba-api library (unofficial but well-maintained)
- Cache team data for efficiency
- Handle API inconsistencies gracefully
- Return normalized data structures

### 4. Analysis Layer (`analyzers/`)

**Purpose**: AI-powered content analysis and formatting.

#### InjuryDetector (`injury_detector.py`)

**Responsibilities**:
- Analyze tweets for injury-related content using AI
- Generate appropriate commentary for reposts
- Provide confidence scores for decisions

**Algorithm**:
1. Send tweet text to OpenAI GPT-4o-mini
2. Use specialized system prompt for injury detection
3. Request structured JSON response
4. Parse confidence level and reasoning
5. Only repost if confidence ≥ 70%

**Design Decisions**:
- Use GPT-4o-mini for cost-effectiveness
- Low temperature (0.3) for consistent analysis
- Structured JSON output for reliability
- Conservative confidence threshold

**Prompt Engineering**:
```
System: "You are an NBA injury news analyst..."
- Includes explicit injury criteria
- Requests specific JSON format
- Emphasizes professional tone

User: "Analyze this tweet: [tweet_text]"
```

#### BoxScoreFormatter (`box_score_formatter.py`)

**Responsibilities**:
- Format game data into tweet-friendly text
- Include top performers when available
- Handle multiple game summaries
- Ensure tweets fit 280-character limit

**Methods**:
- `format_game_summary()`: Basic score display
- `format_game_with_top_performers()`: Include player stats
- `format_multiple_games()`: Daily summary format

**Design Decisions**:
- Fallback to simpler format if too long
- Use emojis for visual appeal (🏀 ⭐)
- Prioritize readability over completeness

### 5. Agent Layer (`agents/`)

**Purpose**: Orchestrate business logic and coordinate between components.

#### TweetMonitorAgent (`tweet_monitor.py`)

**Workflow**:
1. Query database for last processed tweet ID
2. Fetch new tweets since that ID
3. For each tweet:
   - Check if already processed (database lookup)
   - Analyze for injury content (AI)
   - If injury-related with high confidence:
     - Retweet the original tweet
     - Record in database
   - Save processing record

**Design Decisions**:
- Use `since_id` for efficient polling
- Process tweets in chronological order
- Transaction-based processing (rollback on error)
- Idempotent operations (safe to re-run)

#### BoxScoreAgent (`box_score_agent.py`)

**Workflow**:
1. Fetch completed games from today
2. For each game:
   - Check if already posted (database lookup)
   - Fetch detailed box score
   - Extract top performers
   - Format into tweet
   - Post to Twitter
   - Record in database

**Design Decisions**:
- Only post completed games (status == "Final")
- Include top performers for engagement
- One post per game (prevent duplicates)
- Graceful handling of missing data

### 6. Scheduler Layer (`scheduler/`)

**Purpose**: Execute periodic tasks reliably.

#### JobScheduler (`job_scheduler.py`)

**Jobs**:
1. **Tweet Monitor Job**
   - Interval: Configurable (default: 5 minutes)
   - Action: Check for new injury tweets
   - Error Handling: Log and continue

2. **Box Score Job**
   - Interval: Configurable (default: 60 minutes)
   - Action: Post completed game scores
   - Error Handling: Log and continue

**Design Decisions**:
- Use APScheduler with BackgroundScheduler
- Run initial jobs immediately on startup
- Separate job wrappers for error isolation
- Jobs are independent (one failure doesn't affect others)
- Configurable intervals via environment variables

**Scheduler Lifecycle**:
```
Initialize → Setup Jobs → Start → [Running] → Stop
                            ↓
                      Initial Run (immediate)
                            ↓
                      Periodic Runs
```

### 7. Application Layer (`main.py`)

**Purpose**: Application lifecycle management and coordination.

**NBAAgent Class**:

**Setup Phase**:
1. Validate configuration
2. Initialize database (create tables)
3. Initialize API clients
4. Initialize AI analyzers
5. Create agent instances
6. Create scheduler

**Run Phase**:
1. Register signal handlers (SIGINT, SIGTERM)
2. Start scheduler
3. Keep main thread alive
4. Monitor for shutdown signals

**Shutdown Phase**:
1. Stop scheduler
2. Complete in-flight operations
3. Close database connections
4. Exit cleanly

**Design Decisions**:
- Graceful shutdown on Ctrl+C or kill signal
- Comprehensive startup logging
- Fail-fast on configuration errors
- Single entry point for entire application

## Data Flow

### Injury Tweet Monitoring Flow

```
1. Scheduler triggers TweetMonitorAgent
        ↓
2. Query database for last processed tweet_id
        ↓
3. TwitterClient fetches new tweets (since_id)
        ↓
4. For each tweet:
        ↓
5. InjuryDetector analyzes content (OpenAI API)
        ↓
6. If injury-related (confidence ≥ 70%):
        ↓
7. TwitterClient reposts tweet
        ↓
8. Save ProcessedTweet record to database
```

### Box Score Posting Flow

```
1. Scheduler triggers BoxScoreAgent
        ↓
2. NBAClient fetches completed games (today)
        ↓
3. For each game:
        ↓
4. Query database: already posted?
        ↓
5. If not posted:
        ↓
6. NBAClient fetches detailed box score
        ↓
7. BoxScoreFormatter creates tweet text
        ↓
8. TwitterClient posts tweet
        ↓
9. Save BoxScorePost record to database
```

## Error Handling Strategy

### Levels of Error Handling

1. **Client Level**
   - Catch API-specific exceptions
   - Log errors with context
   - Return None or empty list on failure
   - Enable automatic rate limit handling

2. **Agent Level**
   - Wrap operations in try-except
   - Rollback database transactions on error
   - Continue processing other items
   - Log errors with full stack trace

3. **Scheduler Level**
   - Isolate jobs (one failure doesn't stop others)
   - Log job failures
   - Continue scheduling future runs

4. **Application Level**
   - Catch fatal errors
   - Graceful shutdown on critical failures
   - Log final state before exit

## Scalability Considerations

### Current Design (Single Instance)
- Suitable for monitoring 1-5 accounts
- SQLite works well for development
- Can handle ~1000 tweets/day

### Scaling Up (Production)

**Database**:
- Migrate to PostgreSQL for concurrent access
- Add connection pooling
- Consider read replicas for analytics

**Processing**:
- Add message queue (Redis/RabbitMQ)
- Separate worker processes per agent type
- Horizontal scaling of worker pools

**Monitoring**:
- Add Prometheus metrics
- Set up Grafana dashboards
- Alert on error rates

**Deployment**:
- Containerize with Docker
- Use Kubernetes for orchestration
- Implement health checks

## Security Considerations

1. **API Keys**
   - Store in environment variables
   - Never commit to version control
   - Rotate regularly

2. **Database**
   - Use parameterized queries (SQLAlchemy ORM)
   - Sanitize user inputs
   - Regular backups

3. **Rate Limiting**
   - Respect API rate limits
   - Implement exponential backoff
   - Monitor usage

4. **Content Safety**
   - Review AI-generated content
   - Implement content filtering
   - Maintain moderation logs

## Future Enhancements

### Short Term
- Add unit tests and integration tests
- Implement health check endpoint
- Add metrics collection
- Create admin dashboard

### Medium Term
- Support multiple Twitter accounts
- Add webhook support for real-time processing
- Implement content moderation filters
- Add support for images in tweets

### Long Term
- Support for other social platforms (Bluesky, Mastodon)
- Advanced analytics and insights
- Machine learning for better injury detection
- Natural language generation for more engaging tweets

## Monitoring and Observability

### Current Implementation
- File-based logging (daily rotation)
- Console output for real-time monitoring
- Database records of all operations

### Recommended Additions
- Structured logging (JSON format)
- Metrics collection (Prometheus)
- Distributed tracing (Jaeger)
- Error tracking (Sentry)
- Uptime monitoring (UptimeRobot)

## Testing Strategy

### Unit Tests
- Test each client method independently
- Mock external API calls
- Test database operations with in-memory DB
- Test formatters and analyzers

### Integration Tests
- Test agent workflows end-to-end
- Use test Twitter account
- Mock OpenAI API responses
- Verify database state

### End-to-End Tests
- Run full application in test mode
- Verify scheduling works correctly
- Test graceful shutdown
- Verify error recovery

## Deployment Architecture

### Development
```
Local Machine
├── SQLite Database
├── Python Application
└── Log Files
```

### Production
```
Cloud Server (AWS/GCP/Azure)
├── PostgreSQL Database (managed)
├── Docker Container
│   └── NBA Agent Application
├── Log Aggregation (CloudWatch/Stackdriver)
└── Monitoring (Prometheus + Grafana)
```

## Conclusion

The NBA Agent architecture is designed to be:
- **Modular**: Each component has a single responsibility
- **Scalable**: Can grow from single instance to distributed system
- **Maintainable**: Clear separation of concerns
- **Reliable**: Comprehensive error handling and logging
- **Extensible**: Easy to add new features or data sources

The architecture follows software engineering best practices and is production-ready with appropriate scaling considerations.

