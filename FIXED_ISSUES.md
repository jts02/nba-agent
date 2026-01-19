# Fixed Issues - Smart Heat Bot

## ✅ Issues Fixed

### 1. Timestamp Parsing Error (Line 157)
**Problem**: `str object cannot be interpreted as integer` when parsing tweet timestamps

**Fix**:
- Added robust timestamp parsing with try/except
- Checks if timestamp is a string before parsing
- Falls back to `None` if parsing fails
- Individual tweet errors don't crash the whole account scrape

### 2. Immediate Rate Limiting
**Problem**: Got rate limited after scraping just 2 accounts (Ira Winderman, then Anthony Chiang)

**Fix**:
- Added 2-second delays between scraping each account
- Reduced default tweets per account from 20 → 10
- Better error logging with full tracebacks

---

## 🚀 Updated Commands

### Recommended for Avoiding Rate Limits

**Option 1: Scrape less frequently (BEST)**
```bash
# Check every 60 minutes - gives Twitter API time to reset
venv/bin/python smart_heat_bot.py loop 60 --mode monitor
```

**Option 2: Scrape specific categories**
Instead of scraping all 10 accounts at once, scrape one category at a time:

```bash
# Just beat reporters (3 accounts)
# Modify smart_heat_mcp_server.py to use:
# scrape_heat_twitter(account_category="beat_reporters")
```

**Option 3: Reduce tweets per account even more**
In `smart_heat_mcp_server.py`, change line 57:
```python
max_tweets_per_account: int = 5,  # Reduced from 10
```

---

## 🎯 Rate Limit Strategy

Twitter API has limits on:
- Number of requests per 15-minute window
- Number of tweets fetched

**Current bot behavior**:
- Scrapes 10 accounts
- 10 tweets per account = 100 tweets total
- 2-second delays between accounts = 20 seconds total delay
- Total time: ~20-30 seconds per scrape

**Why you got rate limited**:
- Twitter API has strict limits
- Scraping 2 accounts back-to-back triggered it
- Need longer intervals between full scrapes

**Best practices**:
1. **Use 60+ minute intervals** for monitor mode
2. **Scrape during off-peak hours** (less API load)
3. **Consider scraping beat reporters and influencers separately**
4. **The bot works with cached data** - doesn't need constant fresh scrapes

---

## 🔧 Code Changes Made

### smart_heat_mcp_server.py

**Added**:
```python
import time  # For delays between accounts
```

**Wrapped tweet processing in try/except**:
```python
for tweet in tweets:
    try:
        # ... process tweet ...
    except Exception as tweet_error:
        logger.error(f"Error processing tweet: {tweet_error}")
        continue  # Skip this tweet, continue with others
```

**Safe timestamp parsing**:
```python
tweet_created_at = None
if tweet.get('created_at'):
    try:
        created_at_str = tweet.get('created_at')
        if isinstance(created_at_str, str):
            created_at_str = created_at_str.replace('Z', '+00:00')
            tweet_created_at = datetime.fromisoformat(created_at_str)
    except Exception as ts_error:
        logger.warning(f"Could not parse timestamp: {ts_error}")
```

**Added delays between accounts**:
```python
# Add delay between accounts to avoid rate limits (2 seconds)
if accounts_attempted < len(accounts_to_scrape):
    logger.info(f"Waiting 2 seconds before next account...")
    time.sleep(2)
```

**Better error logging**:
```python
except Exception as account_error:
    logger.error(f"Error scraping @{username}: {account_error}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
```

---

## 📋 Recommended Workflow Now

### For Building Initial Memory:
```bash
# Run overnight with 60-minute intervals
# This will scrape ~8-10 times in 10 hours
venv/bin/python smart_heat_bot.py loop 60 --mode monitor
```

### After Memory is Built:
```bash
# Auto mode with moderate frequency
venv/bin/python smart_heat_bot.py loop 30
```

---

## 🛡️ If You Still Get Rate Limited

The bot handles it gracefully now:

1. **Saves partial data** - Any tweets scraped before rate limit are saved
2. **Clear message** - Tells you to wait 15 minutes
3. **Continues working** - Can still tweet using existing database context

**When rate limited**:
- Wait 15 minutes
- Use longer intervals (60+ minutes)
- Or scrape specific categories instead of "all"

---

## ✅ Testing the Fixes

Try running monitor mode again:
```bash
venv/bin/python smart_heat_bot.py --mode monitor
```

**Expected behavior**:
- Scrapes Ira Winderman
- Waits 2 seconds
- Scrapes Anthony Chiang
- Waits 2 seconds
- Continues with other accounts
- If timestamp errors, logs warning but continues
- If rate limited, saves what it got and stops gracefully

---

## 📊 What to Expect

**Successful run**:
```
Scraping @IraHeatBeat...
✅ Got 10 tweets
Waiting 2 seconds before next account...
Scraping @Anthony_Chiang...
✅ Got 10 tweets
Waiting 2 seconds before next account...
...
✅ Successfully scraped 10 accounts
Total: 85 tweets (45 new, 40 updated)
```

**If rate limited**:
```
Scraping @IraHeatBeat...
✅ Got 10 tweets
Waiting 2 seconds before next account...
Scraping @Anthony_Chiang...
⚠️ Rate limited while scraping @Anthony_Chiang
✅ Saved 10 tweets from 1 account before rate limit
⚠️ RATE LIMITED - Wait 15 minutes before scraping again
```

The bot is now much more resilient! Try running it again with the 60-minute interval to avoid rate limits.
