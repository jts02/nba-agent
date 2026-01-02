#!/usr/bin/env python3
"""
Test Twitter authentication in detail.
"""
import tweepy
from config import settings

print("=" * 70)
print("TWITTER AUTHENTICATION TEST")
print("=" * 70)

# Test 1: Try to create client
print("\n1. Creating Tweepy client...")
try:
    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        consumer_key=settings.TWITTER_API_KEY,
        consumer_secret=settings.TWITTER_API_SECRET,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )
    print("   ✅ Client created successfully")
except Exception as e:
    print(f"   ❌ Failed to create client: {e}")
    exit(1)

# Test 2: Try to get authenticated user info (verify credentials)
print("\n2. Testing authentication (getting your account info)...")
try:
    me = client.get_me()
    if me.data:
        print(f"   ✅ Authentication successful!")
        print(f"   📱 Account: @{me.data.username}")
        print(f"   👤 Name: {me.data.name}")
        print(f"   🆔 ID: {me.data.id}")
    else:
        print("   ⚠️  Authentication returned no data")
except tweepy.Forbidden as e:
    print(f"   ❌ 403 Forbidden: {e}")
    print("\n   This means your app doesn't have the right permissions.")
    print("   Fix:")
    print("   1. Go to https://developer.twitter.com/en/portal/dashboard")
    print("   2. Click your app")
    print("   3. Go to 'Settings' tab")
    print("   4. Find 'User authentication settings'")
    print("   5. Make sure 'App permissions' is set to 'Read and Write'")
    print("   6. Save and regenerate your Access Token and Secret")
except tweepy.Unauthorized as e:
    print(f"   ❌ 401 Unauthorized: {e}")
    print("\n   This means one of your credentials is wrong or doesn't match.")
    print("   Common causes:")
    print("   - Access Token and API Key are from different apps")
    print("   - You regenerated tokens but copied the old ones")
    print("   - Tokens were revoked")
    print("\n   Fix:")
    print("   1. Go to https://developer.twitter.com/en/portal/dashboard")
    print("   2. Click your app")
    print("   3. Go to 'Keys and tokens' tab")
    print("   4. Under 'Access Token and Secret', click 'Regenerate'")
    print("   5. Copy BOTH the new Access Token AND Access Token Secret")
    print("   6. Make sure API Key and Secret are from the SAME app")
    print("   7. Update your .env file")
    print("   8. Try again")
except Exception as e:
    print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")

# Test 3: Check app permissions (if we got this far)
print("\n3. Checking what we can do...")
try:
    # Try to read recent tweets (should work with just bearer token)
    print("   Testing READ access (get recent tweets)...")
    tweets = client.search_recent_tweets(query="NBA", max_results=10)
    if tweets.data:
        print(f"   ✅ READ access works (found {len(tweets.data)} tweets)")
    else:
        print("   ⚠️  READ returned no data")
except Exception as e:
    print(f"   ❌ READ failed: {e}")

print("   Testing WRITE access (attempting to post a test tweet)...")
response = input("   Do you want to post a test tweet? (yes/no): ").strip().lower()
if response in ['yes', 'y']:
    try:
        test_tweet = "🤖 Testing NBA Bot - please ignore! This tweet will be deleted."
        result = client.create_tweet(text=test_tweet)
        if result.data:
            tweet_id = result.data['id']
            print(f"   ✅ WRITE access works! Posted test tweet: {tweet_id}")
            print(f"   View at: https://twitter.com/{me.data.username}/status/{tweet_id}")
            
            # Offer to delete it
            delete_response = input("   Delete test tweet? (yes/no): ").strip().lower()
            if delete_response in ['yes', 'y']:
                client.delete_tweet(tweet_id)
                print("   🗑️  Test tweet deleted!")
        else:
            print("   ⚠️  Posted but got no response data")
    except tweepy.Forbidden as e:
        print(f"   ❌ 403 Forbidden: {e}")
        print("\n   🚨 YOUR ACCESS TOKEN DOESN'T HAVE WRITE PERMISSIONS!")
        print("   This happens when you set 'Read and Write' but didn't regenerate tokens.")
        print("\n   FIX:")
        print("   1. Go to https://developer.twitter.com/en/portal/dashboard")
        print("   2. Click your app → 'Keys and tokens' tab")
        print("   3. Click 'Regenerate' under 'Access Token and Secret'")
        print("   4. Copy the NEW tokens (they now have Read+Write)")
        print("   5. Update your .env file")
        print("   6. Run this test again")
    except Exception as e:
        print(f"   ❌ WRITE failed: {type(e).__name__}: {e}")
else:
    print("   ⏭️  Skipped write test")

print("\n" + "=" * 70)
print("RECOMMENDATIONS:")
print("=" * 70)

print("""
If you see 401 Unauthorized above:
1. Go to Twitter Developer Portal
2. Make sure API Key/Secret and Access Token/Secret are from the SAME app
3. Regenerate Access Token and Secret with Read+Write permissions
4. Update your .env file with the NEW tokens
5. Run this script again

If you see 403 Forbidden:
1. Go to your app's User authentication settings
2. Set App permissions to 'Read and Write'
3. Save changes
4. Regenerate Access Token and Secret
5. Update .env and try again

If authentication succeeded:
- You should be able to post tweets!
- Try running: python test_boxscore.py
""")

print("=" * 70)

