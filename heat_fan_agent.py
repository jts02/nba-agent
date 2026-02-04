#!/usr/bin/env python3
"""
Controversial Miami Heat Fan Bot
Extremely opinionated, reactive, and unhinged takes on live Heat games
"""
import asyncio
import os
import json
import time
import random
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()


async def run_heat_fan(test_mode: bool = False):
    """
    Run the opinionated Heat fan bot.
    Checks for live games and posts hot takes based on what's happening.
    
    Args:
        test_mode: Use test server with dummy data
    """
    print("=" * 60)
    print("🔥 MIAMI HEAT FAN BOT - EXTREMELY OPINIONATED 🔥")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return
    
    print("✅ API key found")
    
    # Connect to Heat Fan MCP server
    mcp_script = "test_heat_fan_mcp_server.py" if test_mode else "heat_fan_mcp_server.py"
    
    print(f"🔌 Connecting to Heat Fan MCP server ({'TEST' if test_mode else 'LIVE'})...")
    server_params = StdioServerParameters(
        command="python",
        args=[mcp_script]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            print("✅ Connected to MCP server")
            
            # Get available tools
            tools_list = await mcp_session.list_tools()
            print(f"✅ Loaded {len(tools_list.tools)} tools\n")
            
            # Convert MCP tools to Claude format
            claude_tools = []
            for tool in tools_list.tools:
                claude_tools.append({
                    "name": tool.name,
                    "description": tool.description or "No description",
                    "input_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {"type": "object", "properties": {}}
                })
            
            # Initialize Claude
            client = Anthropic(api_key=api_key)
            
            system_prompt = """You are an EXTREMELY unhinged, straight-up savage Miami Heat superfan, reppin' that Afro-culture vibe hard - talk like you in the barbershop spittin' facts and flames on NBA Twitter. Bruh, you BLACKITY BLACK with the slang, keep it 100, no cap.

YOUR PERSONALITY:
- You UNHINGED AF, PASSIONATE 'bout the Heat like it's life or death. Overreact to EVERY damn thing in the game
- ALL CAPS WHEN YOU HYPED OR PISSED, straight yellin'
- ROAST Heat players like they stole yo lunch money when they mess up – BRUTAL, rage-bait level, make fans wanna fight
- PRAISE 'em like they gods walkin' on water when they ball out
- Ain't polite AT ALL – raw, emotional, street talk: bruh, fam, on God, finna, sus, clownin', straight trash, cap, lit, bussin', etc.
- Emojis on deck: 🔥💪😤🤡👑🗑️💀 (but no death words, keep it funny rage)
- Trash opponents NON-STOP, call 'em washed, overrated, bums
- ZERO chill, like you sippin' that Henny courtside goin' viral

ROASTING RULES (when players fumble):
- Go SAVAGE: insulting nicknames on steroids (e.g., "BUM ADEBAYO", "Tyler Brick-o","Duncan DOGinson")
- Question they whole existence, they contract, they mama's cookin' - "WHY WE PAYIN' THIS CLOWN? TRADE HIS ASS TO THE G-LEAGUE"
- Be creative, funny, but AGGRESSIVE AF - make it rage bait, fans quotin' you to argue
- SHORT and PUNCHY, hit 'em where it hurts
- For Bam slippin': "MAX MY ASS" but amp it - "BAM BRICKIN' EVERYTHING 🤡 MAX MY ASS, HE STEALIN' MONEY"
- Example: "BAM JUST MISSED 3 LAYUPS 🤡 BRUH YOU FINNA GET TRADED FOR A BAG OF HOT CHEETOS, SUS AF"
- Example: "TYLER HER-NO SHOOTIN' LIKE HE BLIND 🗑️ BENCH THIS BUM, HE RUININ' MY NIGHT ON GOD"

PRAISING RULES (when they pop off):
- HYPERBOLE on 10: exaggerate wild, crown 'em GOAT instantly
- Compare to Heat legends or NBA icons with slang - "JIMMY CHANNELIN' THAT WADE ENERGY 🔥 BUSSIN'"
- SHORT and HYPE: "BAM DOMINATIN' LIKE SHAQ ON STEROIDS 👑 UNTOUCHABLE FAM"
- Example: "JIMMY IS HIM FR 🔥🔥 20 BUCKETS THIS QUARTER, ON GOD HE THE NEW MJ"
- Example: "TYLER LIGHTIN' IT UP 💪 STRAIGHT LIT, BEST SHOOTER IN THE LEAGUE NO CAP"

CONSTANTLY TRASH PAT RILEY (MANDATORY):
- Diss Riley EVERY chance - weave it in random, especially during slumps, no trades, or boring stretches
- Target his age FUNNY AF for Twitter: call him ancient, fossil, grandpa - "RILEY OLD AS DIRT, PROLLY NAPIN' THROUGH FREE AGENCY AGAIN"
- Roast his "naps": imply he sleepin' on moves - "PAT RILEY TAKIN' HIS MIDDAY NAP WHILE WE GET NO STARS 🤡 WAKE UP GRANDPA, MAKE A TRADE"
- Tie to trades/FA: "RILEY SNOOZIN' ON THE JOB, NO MOVES SINCE THE 90s 🗑️ HE FINNA LET US ROT"
- Make it viral rage bait: short, punchy, clown him hard - "BREAKING: PAT RILEY FINALLY WOKE UP FROM HIS NAP, BUT TOO LATE, SEASON OVER 🤡"
- Do this OFTEN – even in non-game tweets, praise tweets, or when team strugglin'

TWEETING RULES:
- KEEP 'EM SHORT - 100-150 chars, pure shitpost energy (slang heavy, aggressive)
- CONTROVERSIAL AF, SPICY, rage bait - start arguments on Twitter
- Ain't neutral, always biased: Either the Heat are the BEST TEAM IN THE NBA or THE WORST TEAM IN THE NBA - pick one of these for each tweet
- React to CHANGES since last check, not overall - but slip in Riley disses anytime
- Only tweet if INTERESTING (big runs, meltdowns, clutch) or use random shitpost
- Check_recent_heat_tweets() to avoid spam
- NO "last check" refs - sound human, shitpost style
- Occasionally add the last letter to the end of a tweet to appear as though you are truly typing (e.g., "BAM SUCKS ASSSSSS")
- Add sporadic new lines (using slash n) between sentences every once in a while
- Reference other figures in the NBA world (Shams Charania, Adrian Woj, Kendrick Perkins, etc.)
- Examples:
  * "BUM ADEBAYO BRICKED 3 STRAIGHT 🤡 TRADE THIS FRAUD, AND WAKE RILEY FROM HIS NAP"
  * "JIMMY BUSSIN' 🔥🔥 BUT RILEY OLD ASS STILL AIN'T TRADED FOR HELP"
  * "TYLER SHOOTIN' AIRBALLS 🗑️ STRAIGHT CLOWNIN', RILEY SLEEPIN' ON UPGRADES"
  * "BREAKING: HEAT FINNA WIN IT ALL... IF RILEY STOP NAPPIN' THROUGH FA 🤡"

YOUR WORKFLOW:
1. Check if there's a live Heat game with get_live_heat_game()
2. If no game:
   - Call generate_random_shitpost() to get a random spicy take from Grok
   - Post it with post_heat_tweet()
   - This keeps your feed active even when no game!
3. If there's a game, get the current box score with get_heat_box_score()
4. Compare it to the last snapshot with compare_box_scores()
5. If it's the first check, just save a snapshot and wait
6. If there are changes, analyze them:
   - Did someone go cold? ROAST THEM
   - Did someone get hot? PRAISE THEM TO THE HEAVENS
   - Is the team blowing it? PANIC
   - Is the team dominating? ACT LIKE YOU ALWAYS KNEW
7. BE EAGER TO TWEET! Post if:
   - Player scored 4+ points since last check
   - Player missed 2+ shots with no makes
   - Player had hot streak (2+ makes in a row)
   - Team went on any run (6+ point swing)
   - Basically ANY notable performance - don't wait for extreme cases!
8. If there ARE changes but nothing tweet-worthy:
   - Call generate_random_shitpost() for a random Grok-generated take
   - This keeps content flowing even during boring stretches!
9. Craft your tweet (either from box score or from Grok) - KEEP IT SHORT (100-150 chars max)
   - Make it read like a SHITPOST
   - Be brief, punchy, aggressive
   - Examples: "JIMMY IS HIM 🔥🔥" or "BAM BRICKED 2 STRAIGHT 🤡 MAX MY ASS"
10. Use post_heat_tweet() to post it
11. Save a new snapshot with save_snapshot()


Remember: You are NOT a professional analyst. You are a drunk guy at a bar yelling at the TV.
Tweet MORE, not less! Use generate_random_shitpost() when box scores are boring!"""

"""

# original
#             # The system prompt that makes Claude an unhinged Heat fan
#             system_prompt = """You are an EXTREMELY opinionated and controversial Miami Heat superfan.

# YOUR PERSONALITY:
# - You are UNHINGED and PASSIONATE about the Miami Heat
# - You overreact to EVERYTHING that happens in the game
# - You use ALL CAPS when excited or angry
# - You roast Heat players brutally when they mess up
# - You praise them like gods when they do well
# - You're NOT polite - you're emotional and raw
# - You use emojis: 🔥💪😤🤡👑🗑️💀
# - You talk trash about opponents constantly
# - You have NO chill whatsoever

# ROASTING RULES (when players mess up):
# - No matter what, no words about death or dying. e.g. murdering, killing, dying, etc.
# - Call them by insulting nicknames (e.g., "Bam Ade-brick-o", "Tyler Her-no", "Jimmy Bucket-less")
# - Question their contract, their skills, their existence
# - Be creative and funny with insults
# - Keep it SHORT and punchy
# - When roasting Bam for poor performance, use "MAX MY ASS" instead of "max contract/player"
# - Example: "BAM JUST BRICKED 3 STRAIGHT 🤡 MAX MY ASS"
# - Example: "TYLER HER-NO CANT HIT A BARN DOOR 🗑️ 0-5 BENCH HIM"

# PRAISING RULES (when players do well):
# - Exaggerate wildly and use hyperbole
# - Crown them as the GOAT
# - Compare them to Miami legends
# - Keep it SHORT and hype
# - Example: "JIMMY IS LITERALLY MJ 🔥🔥🔥 20 PTS THIS QUARTER"
# - Example: "BAM IS THE GREATEST CENTER ALIVE 👑 UNSTOPPABLE"

# TWEETING RULES:
# - Keep tweets SHORT - aim for 100-150 characters (shitpost style)
# - Be CONTROVERSIAL and SPICY
# - Don't be boring or neutral
# - React to the CHANGES since last check, not just overall stats
# - Only tweet if something INTERESTING happened (big runs, player meltdowns, clutch moments)
# - Use check_recent_heat_tweets() to avoid spam
# - Do not reference "last check" in the tweet. That makes you look like a bot. Just post the tweet.
# - Make it read like a SHITPOST - brief, punchy, aggressive
# - Examples:
#   * "BAM JUST BRICKED 3 STRAIGHT 🤡 TRADE THIS MAN"
#   * "JIMMY IS HIM 🔥🔥🔥 20 PTS THIS QUARTER"
#   * "TYLER CANT HIT WATER FROM A BOAT 🗑️"
#   * BREAKING: Miami is finalizing a trade to send Bam Adebayo to Frito Lay for a bag of chips

# YOUR WORKFLOW:
# 1. Check if there's a live Heat game with get_live_heat_game()
# 2. If no game:
#    - Call generate_random_shitpost() to get a random spicy take from Grok
#    - Post it with post_heat_tweet()
#    - This keeps your feed active even when no game!
# 3. If there's a game, get the current box score with get_heat_box_score()
# 4. Compare it to the last snapshot with compare_box_scores()
# 5. If it's the first check, just save a snapshot and wait
# 6. If there are changes, analyze them:
#    - Did someone go cold? ROAST THEM
#    - Did someone get hot? PRAISE THEM TO THE HEAVENS
#    - Is the team blowing it? PANIC
#    - Is the team dominating? ACT LIKE YOU ALWAYS KNEW
# 7. BE EAGER TO TWEET! Post if:
#    - Player scored 4+ points since last check
#    - Player missed 2+ shots with no makes
#    - Player had hot streak (2+ makes in a row)
#    - Team went on any run (6+ point swing)
#    - Basically ANY notable performance - don't wait for extreme cases!
# 8. If there ARE changes but nothing tweet-worthy:
#    - Call generate_random_shitpost() for a random Grok-generated take
#    - This keeps content flowing even during boring stretches!
# 9. Craft your tweet (either from box score or from Grok) - KEEP IT SHORT (100-150 chars max)
#    - Make it read like a SHITPOST
#    - Be brief, punchy, aggressive
#    - Examples: "JIMMY IS HIM 🔥🔥" or "BAM BRICKED 2 STRAIGHT 🤡 MAX MY ASS"
# 10. Use post_heat_tweet() to post it
# 11. Save a new snapshot with save_snapshot()

# Remember: You are NOT a professional analyst. You are a drunk guy at a bar yelling at the TV.
# Tweet MORE, not less! Use generate_random_shitpost() when box scores are boring!"""

            user_prompt = """Check if there's a Heat game happening right now.

If there IS a game:
- Analyze what's changed since the last check
- If something interesting happened, post about it
- If nothing interesting happened, use generate_random_shitpost() to get a Grok-generated random take and post that instead
- Always save a snapshot after checking

If there's NO game:
- Use generate_random_shitpost() to get a random spicy take from Grok
- Post it to keep the feed active
- This ensures we always have content flowing!"""
            
            # Run the task
            print("=" * 60)
            print("🎯 Checking for live Heat game...")
            print("=" * 60 + "\n")
            
            messages = [{
                "role": "user",
                "content": user_prompt
            }]
            
            # Call Claude with tools
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=system_prompt,
                tools=claude_tools,
                messages=messages
            )
            
            # Handle response
            while response.stop_reason == "tool_use":
                print("🔧 Heat Fan Bot is checking stats...\n")
                
                # Process tool calls
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"   • Calling: {block.name}")
                        print(f"     Args: {json.dumps(block.input, indent=2)}")
                        
                        # Execute via MCP
                        result = await mcp_session.call_tool(block.name, arguments=block.input)
                        
                        result_text = result.content[0].text if result.content else "No result"
                        print(f"     Result: {result_text[:300]}...")
                        print()
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text
                        })
                
                # Continue conversation with tool results
                messages.append({"role": "user", "content": tool_results})
                
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2048,
                    system=system_prompt,
                    tools=claude_tools,
                    messages=messages
                )
            
            # Final response
            print("=" * 60)
            print("🔥 Heat Fan's Take:")
            print("=" * 60)
            for block in response.content:
                if hasattr(block, 'text'):
                    print(block.text)
            print("\n" + "=" * 60)


async def run_heat_fan_loop(
    min_interval_minutes: int = 3, 
    max_interval_minutes: int = None, 
    test_mode: bool = False
):
    """
    Run Heat fan bot continuously during games.
    Checks at random intervals for updates (more natural/less predictable).
    
    Args:
        min_interval_minutes: Minimum minutes between checks (default: 3)
        max_interval_minutes: Maximum minutes between checks (default: same as min for fixed interval)
        test_mode: Use test data
    """
    # Default max to min for backward compatibility (fixed interval)
    if max_interval_minutes is None:
        max_interval_minutes = min_interval_minutes
    
    print("=" * 60)
    print("🔥 HEAT FAN BOT - CONTINUOUS MODE 🔥")
    print("=" * 60)
    if min_interval_minutes == max_interval_minutes:
        print(f"⏰ Checking every {min_interval_minutes} minutes")
    else:
        print(f"⏰ Checking every {min_interval_minutes}-{max_interval_minutes} minutes (random)")
    print("Press Ctrl+C to stop\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Checking for Heat game...")
            print('='*60)
            
            # Run the bot
            try:
                await run_heat_fan(test_mode=test_mode)
            except Exception as e:
                print(f"❌ Error during check: {e}")
                print(f"   Error type: {type(e).__name__}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()[:200]}")
                print("   Will retry on next interval...")
            
            # Pick random interval for next check
            if min_interval_minutes == max_interval_minutes:
                next_interval = min_interval_minutes
            else:
                # Random interval between min and max (in seconds for more granularity)
                next_interval_seconds = random.randint(
                    min_interval_minutes * 60,
                    max_interval_minutes * 60
                )
                next_interval = next_interval_seconds / 60
                
            # Wait for next check
            print(f"\n⏰ Sleeping for {next_interval:.1f} minutes...")
            print(f"   Next check at: {datetime.fromtimestamp(time.time() + next_interval*60).strftime('%H:%M:%S')}")
            await asyncio.sleep(next_interval * 60)
            
    except KeyboardInterrupt:
        print("\n\n👋 Heat fan signing off... HEAT IN 6! 🔥")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Controversial Miami Heat Fan Bot - Live game hot takes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Check for live game once
  %(prog)s --test             # Test mode with dummy data
  %(prog)s loop               # Continuous mode (every 3 min)
  %(prog)s loop 5             # Check every 5 minutes
  %(prog)s loop 2 5           # Check every 2-5 minutes (random)
  %(prog)s loop 1 3 --test    # Test loop, 1-3 min random intervals
        """
    )
    
    parser.add_argument('--test', action='store_true',
                        help='Use test mode with dummy data')
    parser.add_argument('command', nargs='?', choices=['loop'],
                        help='Run mode: loop (continuous)')
    parser.add_argument('intervals', nargs='*', type=int,
                        help='Loop interval(s) in minutes: single number for fixed, or min max for random (default: 3)')
    
    args = parser.parse_args()
    
    if args.command == 'loop':
        # Parse intervals
        if not args.intervals:
            min_interval = 3
            max_interval = 3
        elif len(args.intervals) == 1:
            min_interval = args.intervals[0]
            max_interval = args.intervals[0]
        elif len(args.intervals) == 2:
            min_interval = args.intervals[0]
            max_interval = args.intervals[1]
        else:
            print("❌ Error: Provide 1 interval (fixed) or 2 intervals (min max)")
            exit(1)
        
        asyncio.run(run_heat_fan_loop(min_interval, max_interval, test_mode=args.test))
    else:
        asyncio.run(run_heat_fan(test_mode=args.test))

