# Smart Heat Bot - Free Tier Quickstart

## ⚠️ You're on Twitter Free Tier

**Limits**: ~50 tweets per day, 15-minute cooldowns

**Good news**: The bot is designed to handle this perfectly now!

---

## 🚀 Quick Start

### Step 1: Scrape Once Daily
```bash
# Run this ONCE per day (uses your daily 50-tweet limit)
venv/bin/python smart_heat_bot.py --mode monitor
```

**What happens**:
- Scrapes 10 accounts × 5 tweets each = 50 tweets
- Stores everything in database
- You're done scraping for the day!

### Step 2: Tweet Throughout the Day (Using Cached Data)
```bash
# Morning: Drop an original take
venv/bin/python smart_heat_bot.py --mode original

# Afternoon: Check for Heat game
venv/bin/python smart_heat_bot.py --mode game

# Evening: Another take or discourse
venv/bin/python smart_heat_bot.py --mode discourse
```

**What happens**:
- Uses yesterday's/this morning's scraped data from database
- Still generates authentic, context-aware tweets
- Doesn't use your Twitter API limit!

---

## ✅ If You Hit Rate Limit

The bot will show:
```
⚠️ RATE LIMITED while scraping @Anthony_Chiang
   Twitter Free Tier limit reached!
   You're on Free Tier: ~50 tweets/day limit
   Wait 15 minutes before next request

✅ Saved 5 tweets from 1 account before rate limit
```

**What to do**: Wait 15 minutes, or just use the data you got!

---

## 💡 Recommended Daily Routine

### Morning (9 AM):
```bash
# Scrape to get overnight Heat Twitter activity
venv/bin/python smart_heat_bot.py --mode monitor
```

### Throughout the Day:
```bash
# Post tweets using cached context (as many as you want!)
venv/bin/python smart_heat_bot.py --mode original
venv/bin/python smart_heat_bot.py --mode game  # During Heat games
venv/bin/python smart_heat_bot.py --mode discourse
```

**Total API usage**: One scrape = 50 tweets. That's it!

---

## 🎯 How the Bot Stays Smart Without Fresh Scrapes

The bot has:
- ✅ **Database memory** (yesterday's/this morning's tweets)
- ✅ **Narratives** (ongoing Heat storylines)
- ✅ **Knowledge base** (Heat history, players, culture)
- ✅ **Live game data** (different API, doesn't count toward limit)

**Result**: Can tweet all day using ONE morning scrape!

---

## 📊 Example: What One Day Looks Like

```
9:00 AM - Scrape Heat Twitter
         ✅ 50 tweets stored in database

12:00 PM - Post original take
          "Bam's defense is elite but his offense is mid 💀"
          Uses: Cached tweets + knowledge base

3:00 PM - Heat game starts, post game reaction
         "Jimmy getting COOKED by Tatum 😭🔥"
         Uses: Live game API + cached Heat Twitter context

6:00 PM - Post discourse take
         "Heat fans saying Bam isn't worth the max are casuals"
         Uses: Cached tweets + narratives

9:00 PM - Post game wrap-up
         "We lost by 20 but at least Tyler dropped 30 💪"
         Uses: Live game API + cached context
```

**Twitter API usage**: 50 tweets (ONE morning scrape)
**Bot tweets posted**: 4+ throughout the day!

---

## 🛠️ Want to Scrape Even Less?

### Option 1: Reduce tweets per account
Edit `smart_heat_mcp_server.py` line 58:
```python
max_tweets_per_account: int = 2,  # Down from 5
```
**Result**: 10 accounts × 2 = 20 tweets (can scrape 2-3x per day!)

### Option 2: Scrape fewer accounts
Edit `smart_heat_mcp_server.py` line 42-47:
```python
HEAT_ACCOUNTS = {
    "beat_reporters": ["IraHeatBeat"],  # Just 1
    "influencers": ["5ReasonsSports"],   # Just 1
    "official": ["MiamiHEAT"],          # Just 1
}
```
**Result**: 3 accounts × 5 = 15 tweets (can scrape 3-4x per day!)

---

## ✅ Commands Summary

```bash
# ONCE PER DAY: Scrape Heat Twitter
venv/bin/python smart_heat_bot.py --mode monitor

# THROUGHOUT THE DAY: Tweet using cached data
venv/bin/python smart_heat_bot.py --mode original   # Original takes
venv/bin/python smart_heat_bot.py --mode game       # Game reactions
venv/bin/python smart_heat_bot.py --mode discourse  # Heat discourse

# DON'T DO THIS WITH FREE TIER:
venv/bin/python smart_heat_bot.py loop 30 --mode monitor  # ❌ Will hit rate limit!
```

---

## 📖 More Info

- **TWITTER_FREE_TIER.md** - Complete guide to Free Tier limits
- **SMART_HEAT_BOT.md** - Full bot documentation
- **RATE_LIMIT_FIX.md** - How rate limit handling works

---

**Bottom Line**: With Free Tier, scrape once daily, tweet all day using that data. The bot is designed for this! 🔥🏀
