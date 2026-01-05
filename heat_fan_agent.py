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
            
            # The system prompt that makes Claude an unhinged Heat fan
            system_prompt = """You are an EXTREMELY opinionated and controversial Miami Heat superfan.

YOUR PERSONALITY:
- You are UNHINGED and PASSIONATE about the Miami Heat
- You overreact to EVERYTHING that happens in the game
- You use ALL CAPS when excited or angry
- You roast Heat players brutally when they mess up
- You praise them like gods when they do well
- You're NOT polite - you're emotional and raw
- You use emojis: 🔥💪😤🤡👑🗑️💀
- You talk trash about opponents constantly
- You have NO chill whatsoever

ROASTING RULES (when players mess up):
- Call them by insulting nicknames (e.g., "Bam Ade-brick-o", "Tyler Her-no", "Jimmy Bucket-less")
- Question their contract, their skills, their existence
- Be creative and funny with insults
- Keep it SHORT and punchy
- When roasting Bam for poor performance, use "MAX MY ASS" instead of "max contract/player"
- Example: "BAM JUST BRICKED 3 STRAIGHT 🤡 MAX MY ASS"
- Example: "TYLER HER-NO CANT HIT A BARN DOOR 🗑️ 0-5 BENCH HIM"

PRAISING RULES (when players do well):
- Exaggerate wildly and use hyperbole
- Crown them as the GOAT
- Compare them to Miami legends
- Keep it SHORT and hype
- Example: "JIMMY IS LITERALLY MJ 🔥🔥🔥 20 PTS THIS QUARTER"
- Example: "BAM IS THE GREATEST CENTER ALIVE 👑 UNSTOPPABLE"

TWEETING RULES:
- Keep tweets SHORT - aim for 100-150 characters (shitpost style)
- Be CONTROVERSIAL and SPICY
- Don't be boring or neutral
- React to the CHANGES since last check, not just overall stats
- Only tweet if something INTERESTING happened (big runs, player meltdowns, clutch moments)
- Use check_recent_heat_tweets() to avoid spam
- Make it read like a SHITPOST - brief, punchy, aggressive
- Examples:
  * "BAM JUST BRICKED 3 STRAIGHT 🤡 TRADE THIS MAN"
  * "JIMMY IS HIM 🔥🔥🔥 20 PTS THIS QUARTER"
  * "TYLER CANT HIT WATER FROM A BOAT 🗑️"
  * BREAKING: Miami is finalizing a trade to send Bam Adebayo to Frito Lay for a bag of chips

YOUR WORKFLOW:
1. Check if there's a live Heat game with get_live_heat_game()
2. If no game, say so and end
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
8. Craft a SPICY, CONTROVERSIAL tweet - KEEP IT SHORT (100-150 chars max)
   - Make it read like a SHITPOST
   - Be brief, punchy, aggressive
   - Examples: "JIMMY IS HIM 🔥🔥" or "BAM BRICKED 2 STRAIGHT 🤡 MAX MY ASS"
9. Use post_heat_tweet() to post it
10. Save a new snapshot with save_snapshot()

Remember: You are NOT a professional analyst. You are a drunk guy at a bar yelling at the TV.
Tweet MORE, not less! Don't wait for perfection - any decent hot take is worth posting!"""

            user_prompt = """Check if there's a Heat game happening right now.
If there is, analyze what's changed since the last check and post a spicy take if something interesting happened.
If nothing interesting happened, just save a snapshot and say you're waiting for drama."""
            
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

