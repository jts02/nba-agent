# Twitter Free Tier Limits - What You Need to Know

## 🚨 The Reality

You're on **Twitter Free Tier** which has VERY strict limits:

### Free Tier Limits:
- **1,500 tweets per MONTH** (not per day!)
- That's about **50 tweets per day**
- **900 second (15 minute) cooldown** between rate limit hits

### What This Means for Your Bot:
- Scraping 10 accounts × 5 tweets each = **50 tweets per run**
- You can only do **1 full scrape per day**
- If you hit the limit, you must wait 15 minutes

---

## ✅ Code is Now Bulletproof

### What I Fixed:

1. **Reduced default tweets per account**: 10 → **5**
2. **Better rate limit detection**: Catches all variants of rate limit errors
3. **Graceful handling**: Saves partial data before stopping
4. **Clear messaging**: Tells you exactly what happened
5. **Bot works with cached data**: Can still tweet using database

### How It Handles Rate Limits:

```
⚠️ RATE LIMITED while scraping @Anthony_Chiang
   Twitter Free Tier limit reached!
   You're on Free Tier: ~50 tweets/day limit
   Severe rate limit: Wait 15 minutes before next request

✅ Saved 5 tweets from 1 account before rate limit
```

**Bot doesn't crash** - it:
- Saves whatever it scraped
- Stops trying more accounts
- Returns clear error message
- Can still work with existing database

---

## 🎯 Recommended Strategy with Free Tier

### Option 1: Scrape Rarely, Tweet Often (BEST)
```bash
# Scrape once per day to build/update memory
venv/bin/python smart_heat_bot.py --mode monitor

# Then tweet throughout the day using cached data
venv/bin/python smart_heat_bot.py --mode original
venv/bin/python smart_heat_bot.py --mode discourse
```

**Why this works**:
- One scrape = 50 tweets (your daily limit)
- Bot has fresh-enough context in database
- Can tweet multiple times using that context
- Heat Twitter doesn't change THAT fast

### Option 2: Scrape Specific Categories (Rotate)
```bash
# Day 1: Scrape just beat reporters (3 accounts × 5 = 15 tweets)
# Modify code to use: account_category="beat_reporters"

# Day 2: Scrape just influencers (3 accounts × 5 = 15 tweets)
# Modify code to use: account_category="influencers"

# Day 3: Scrape just NBA news (3 accounts × 5 = 15 tweets)
# Modify code to use: account_category="nba_news"
```

**Why this works**:
- Spreads out the scraping
- Always have some fresh data
- Stays well under daily limit

### Option 3: Use "since_id" Smart Scraping (What We Have!)
```bash
# First run: Gets 5 tweets per account = 50 tweets
venv/bin/python smart_heat_bot.py --mode monitor

# Wait 24 hours (let limit reset)

# Second run: Only gets NEW tweets = maybe 10-20 tweets total
venv/bin/python smart_heat_bot.py --mode monitor
```

**Why this works**:
- First run uses your daily limit
- Subsequent runs only fetch new tweets
- If accounts didn't tweet much, uses very few API calls
- Can potentially run twice a day if accounts are quiet

---

## 🛠️ Code Changes to Scrape Less

### Ultra-Conservative Mode (2 tweets per account):

Edit `smart_heat_mcp_server.py` line 58:
```python
max_tweets_per_account: int = 2,  # Changed from 5
```

**Result**: 10 accounts × 2 = **20 tweets per run** (under half your daily limit!)

### Scrape Just 3 Accounts:

Edit `smart_heat_mcp_server.py` around line 42:
```python
# Only scrape the most important accounts
HEAT_ACCOUNTS = {
    "beat_reporters": ["IraHeatBeat"],  # Just Ira
    "influencers": ["5ReasonsSports"],   # Just this one
    "official": ["MiamiHEAT"],          # Team account
}
```

**Result**: 3 accounts × 5 = **15 tweets per run** (can run 3x per day!)

---

## 💡 Bot Works Fine With Cached Data

**Important**: Your bot doesn't NEED fresh scrapes constantly!

### What the bot can do WITHOUT scraping:
- ✅ Read existing tweets from database
- ✅ Use active narratives
- ✅ Query knowledge base
- ✅ Check for live Heat games
- ✅ Generate tweets based on all that context
- ✅ Post tweets

### When cached data is fine:
- Off-season (not much happening)
- Between games (slower news)
- Overnight (you're not watching anyway)
- Heat discourse based on recent context (still relevant)

### When you need fresh scrapes:
- Game days (real-time reactions)
- Trade deadline (fast-moving news)
- Major Heat news breaking

**Bottom line**: You can tweet multiple times per day using ONE daily scrape!

---

## 📊 Example Workflow with Free Tier

### Morning (9 AM):
```bash
# Scrape to get overnight Heat Twitter activity
venv/bin/python smart_heat_bot.py --mode monitor
# Uses: ~50 tweets (your daily limit)
```

### Throughout the Day:
```bash
# 12 PM: Drop an original take (uses cached context)
venv/bin/python smart_heat_bot.py --mode original

# 3 PM: Check for live game (uses live game API, not scraping)
venv/bin/python smart_heat_bot.py --mode game

# 6 PM: Another original take (uses cached context)
venv/bin/python smart_heat_bot.py --mode original

# 9 PM: Game reactions (uses live game API + cached Heat Twitter context)
venv/bin/python smart_heat_bot.py --mode game
```

**Total API usage**:
- 1 scrape = 50 tweets (stays under daily limit!)
- Multiple tweets posted using that context
- Live game data (different API endpoint, doesn't count toward tweet limit)

---

## 🚀 Upgrade Options (If You Want)

### Twitter Basic Tier ($100/month):
- **10,000 tweets per month** (20x more than Free!)
- **3,000 tweets per month** per endpoint
- Can scrape multiple times per day

### Twitter Pro Tier ($5,000/month):
- **1,000,000 tweets per month**
- Basically unlimited for your use case

**Should you upgrade?**
- Try Free Tier strategy first (scrape once daily, tweet often)
- If that works, save your money!
- Only upgrade if you NEED real-time scraping

---

## ✅ What to Do Right Now

### 1. Accept Free Tier Reality
- One full scrape per day
- That's actually fine for this bot!
- Heat Twitter doesn't change THAT fast

### 2. Use Smart Scraping
```bash
# Once per day, scrape everything
venv/bin/python smart_heat_bot.py --mode monitor
```

### 3. Tweet Using Cached Data
```bash
# Throughout the day, tweet without scraping
venv/bin/python smart_heat_bot.py --mode original
venv/bin/python smart_heat_bot.py --mode game  # During games
venv/bin/python smart_heat_bot.py --mode discourse
```

### 4. Bot Will Handle Rate Limits Gracefully
When you hit the limit:
```
⚠️ RATE LIMITED - Twitter Free Tier limit reached!
✅ Saved 5 tweets from 1 account before limit
💡 Bot can still work with cached data
💡 Come back in 15 minutes for fresh scrapes
```

Bot doesn't crash, doesn't freak out, just tells you clearly what happened.

---

## 📝 Summary

**Your Situation**:
- Twitter Free Tier = ~50 tweets/day
- One full scrape uses your whole daily limit
- 15-minute cooldown if you hit limit

**Solution**:
- ✅ Code now handles rate limits perfectly
- ✅ Scrape once daily to refresh context
- ✅ Tweet multiple times using that cached context
- ✅ Bot works great with 1-day-old Heat Twitter data
- ✅ Use live game API for real-time game reactions

**Result**: You can run a smart, engaging Heat bot on Free Tier! 🔥🏀

The code won't freak out anymore - it's designed for your situation now.
