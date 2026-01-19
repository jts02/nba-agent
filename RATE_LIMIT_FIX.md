# Rate Limit Fix & Player Account Removal

## Changes Made

### 1. Removed Player Accounts from Monitoring ✅

**Why**: Players change teams (Jimmy Butler no longer on Heat), so monitoring player accounts doesn't make sense.

**Changed in**: `smart_heat_mcp_server.py`

**Before**:
```python
HEAT_ACCOUNTS = {
    "official": ["MiamiHEAT", "JimmyButler"],  # Had Jimmy Butler
}
```

**After**:
```python
HEAT_ACCOUNTS = {
    "official": ["MiamiHEAT"],  # Only official team account
}
```

Now monitoring only:
- 3 beat reporters
- 3 Heat influencers/fan accounts
- 1 official team account
- 3 NBA news sources
- **Total: 10 accounts (down from 11)**

---

### 2. Added Comprehensive Rate Limit Handling ✅

**Problem**: Twitter API locks you out for 12-15 minutes when scraping too much.

**Solution**: Added intelligent error handling that:
- Detects rate limit errors (429, "rate limit", "too many requests")
- Saves any tweets scraped before the rate limit hit
- Stops trying to scrape more accounts when rate limited
- Returns clear messages: "⚠️ RATE LIMITED - Wait 15 minutes"
- Provides suggestions on how to avoid rate limits

**Changed in**: `smart_heat_mcp_server.py` - `scrape_heat_twitter()` function

**What happens now when rate limited**:
```json
{
  "rate_limited": true,
  "wait_minutes": 15,
  "message": "⚠️ RATE LIMITED after 3/10 accounts. Wait 15 minutes before scraping again.",
  "suggestion": "Consider: 1) Reduce max_tweets_per_account, 2) Scrape specific categories, 3) Increase time between scrapes",
  "accounts_succeeded": 3,
  "total_tweets": 45,
  "new_tweets": 12
}
```

**The bot can still function** even when rate limited because:
- It has memory from previous scrapes in the database
- Can use `get_heat_twitter_context()` to access existing data
- Can still tweet based on narratives and knowledge base
- Just won't have the absolute latest tweets

---

### 3. Reduced Default Tweets Per Account ✅

**Changed**: Default `max_tweets_per_account` from **20 → 10**

**Why**: Lower chance of hitting rate limits. 10 tweets per account is still plenty for learning context.

**Math**:
- Old: 11 accounts × 20 tweets = 220 API calls
- New: 10 accounts × 10 tweets = 100 API calls (less than half!)

---

### 4. Updated Bot to Handle Rate Limits Gracefully ✅

**Changed in**: `smart_heat_bot.py` - System prompt

**Added instructions**:
- If scrape returns `rate_limited: true`, DON'T try to scrape again
- Use existing database context instead
- Can still tweet based on narratives, knowledge, and cached data
- Note in summary that working with cached data

**Before**: Bot might keep trying to scrape and fail repeatedly

**After**: Bot recognizes rate limit, uses cached data, continues working

---

### 5. Updated Documentation ✅

**Changed in**: `SMART_HEAT_BOT.md`

Added comprehensive "Twitter API rate limits" section with:
- How the bot handles rate limits
- How to avoid rate limits (4 strategies)
- What to do if rate limited
- Reassurance that bot still works with cached data

---

## How to Avoid Rate Limits

### Strategy 1: Reduce Tweets Per Account
The default is now 10 instead of 20. You can reduce further if needed.

### Strategy 2: Scrape Specific Categories
Instead of scraping all 10 accounts at once, scrape one category:
- `account_category="beat_reporters"` (3 accounts)
- `account_category="influencers"` (3 accounts)
- `account_category="official"` (1 account)
- `account_category="nba_news"` (3 accounts)

### Strategy 3: Increase Time Between Scrapes
```bash
# Less frequent = less rate limit risk
python smart_heat_bot.py loop 30 --mode monitor  # Every 30 min
python smart_heat_bot.py loop 60 --mode monitor  # Every hour
```

### Strategy 4: Let the Bot Use Cached Data
The bot has memory! Even if you can't scrape for a while, it can still:
- Read existing tweets from database
- Use active narratives
- Query knowledge base
- Generate tweets based on context

---

## Testing the Fixes

### Test Rate Limit Handling
```bash
# Run monitor mode - if you hit rate limit, it will handle gracefully
python smart_heat_bot.py --mode monitor
```

**Expected output if rate limited**:
```
⚠️ RATE LIMITED after 3/10 accounts. Wait 15 minutes before scraping again.
Suggestion: Consider: 1) Reduce max_tweets_per_account, 2) Scrape specific categories instead of 'all', 3) Increase time between scrapes
```

**Bot should**:
- Not crash or error out
- Save whatever tweets it got
- Tell you clearly to wait 15 minutes
- Still be able to use existing database context

### Test With Cached Data
```bash
# After getting rate limited, try to tweet with existing data
python smart_heat_bot.py --mode original
```

**Expected**: Bot uses database context (recent tweets, narratives) to generate tweet without needing fresh scrape.

---

## Summary

✅ **Removed player accounts** (Jimmy Butler) - only monitoring team, reporters, influencers, news
✅ **Added robust rate limit handling** - detects, saves partial data, tells you to wait
✅ **Reduced default API calls** by 55% - 10 tweets/account instead of 20
✅ **Bot works even when rate limited** - uses cached database context
✅ **Clear error messages** - tells you exactly what happened and what to do
✅ **Documentation updated** - comprehensive troubleshooting guide

**Result**: Much more resilient to Twitter API rate limits, and continues working even when limited!
