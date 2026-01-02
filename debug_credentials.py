#!/usr/bin/env python3
"""
Debug script to check what Twitter credentials are being loaded.
"""
from config import settings

print("=" * 70)
print("TWITTER CREDENTIALS DEBUG")
print("=" * 70)

credentials = {
    "TWITTER_API_KEY": settings.TWITTER_API_KEY,
    "TWITTER_API_SECRET": settings.TWITTER_API_SECRET,
    "TWITTER_ACCESS_TOKEN": settings.TWITTER_ACCESS_TOKEN,
    "TWITTER_ACCESS_TOKEN_SECRET": settings.TWITTER_ACCESS_TOKEN_SECRET,
    "TWITTER_BEARER_TOKEN": settings.TWITTER_BEARER_TOKEN,
}

for name, value in credentials.items():
    if value:
        # Show first and last 4 characters to verify without exposing full key
        if len(value) > 8:
            masked = f"{value[:4]}...{value[-4:]}"
        else:
            masked = "****"
        print(f"✅ {name:30} = {masked} (length: {len(value)})")
        
        # Check for common issues
        if value.startswith('"') or value.startswith("'"):
            print(f"   ⚠️  WARNING: Starts with a quote - remove quotes from .env!")
        if value.endswith('"') or value.endswith("'"):
            print(f"   ⚠️  WARNING: Ends with a quote - remove quotes from .env!")
        if value.startswith(' ') or value.endswith(' '):
            print(f"   ⚠️  WARNING: Has extra spaces - remove spaces from .env!")
        if '\n' in value or '\r' in value:
            print(f"   ⚠️  WARNING: Contains newline characters!")
    else:
        print(f"❌ {name:30} = MISSING")

print("\n" + "=" * 70)
print("EXPECTED FORMATS:")
print("=" * 70)
print("API_KEY:              Usually ~25 characters")
print("API_SECRET:           Usually ~50 characters")
print("ACCESS_TOKEN:         Format: numbers-letters (with hyphen)")
print("ACCESS_TOKEN_SECRET:  Usually ~45 characters")
print("BEARER_TOKEN:         Usually very long (100+ characters)")
print("\n" + "=" * 70)

# Try to show the .env file format (first few lines, masked)
print("\nYour .env file should look like this (NO quotes, NO spaces):")
print("=" * 70)
print("TWITTER_API_KEY=abc123xyz")
print("TWITTER_API_SECRET=verylongsecrethere")
print("TWITTER_ACCESS_TOKEN=1234567890-AbCdEf")
print("TWITTER_ACCESS_TOKEN_SECRET=anotherlongsecret")
print("TWITTER_BEARER_TOKEN=veryveryverylongbearertoken")
print("=" * 70)

