#!/usr/bin/env python3
"""
Simple AI Agent - Direct Claude API + MCP Server

No complex LangChain setup - just Claude + your MCP tools.
"""
import asyncio
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()


async def run_agent(test_mode: bool = False, injury_only: bool = False, box_score_only: bool = False, shams_shitpost: bool = False):
    """Run AI agent with Claude + MCP.
    
    Args:
        test_mode: Use test data instead of real APIs
        injury_only: Only run injury monitoring (not box scores)
        box_score_only: Only run box score posting (not injuries)
        shams_shitpost: Only generate troll shitposts from Shams tweets
        
    By default (no flags), runs BOTH injury and box score monitoring.
    """
    # Determine what to run
    run_injuries = not box_score_only and not shams_shitpost  # Run injuries unless box_score_only or shams_shitpost
    run_box_scores = not injury_only and not shams_shitpost   # Run box scores unless injury_only or shams_shitpost
    
    # Determine mode text
    if test_mode:
        if injury_only:
            mode_text = "🧪 TEST MODE - INJURY MONITORING (Using dummy tweets)"
        elif box_score_only:
            mode_text = "🧪 TEST MODE - BOX SCORES (Using dummy games)"
        elif shams_shitpost:
            mode_text = "🧪 TEST MODE - SHAMS SHITPOSTS (Using dummy tweets)"
        else:
            mode_text = "🧪 TEST MODE - BOX SCORES & INJURIES (Using dummy data)"
    else:
        if injury_only:
            mode_text = "🤖 NBA AI AGENT - INJURY MONITORING"
        elif box_score_only:
            mode_text = "🤖 NBA AI AGENT - BOX SCORES"
        elif shams_shitpost:
            mode_text = "🤖 NBA AI AGENT - SHAMS SHITPOST MODE 🤡"
        else:
            mode_text = "🤖 NBA AI AGENT - BOX SCORES & INJURIES"
    
    print("=" * 60)
    print(mode_text)
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        print("   Set it: export ANTHROPIC_API_KEY=your_key_here")
        return
    
    print("✅ API key found")
    
    # Connect to MCP server based on mode
    if test_mode:
        if injury_only:
            mcp_script = "test_injury_mcp_server.py"
        elif box_score_only:
            mcp_script = "test_mcp_server.py"
        elif shams_shitpost:
            mcp_script = "test_injury_mcp_server.py"  # Has tweets and shitpost tools
        else:
            # Test both - use combined test server
            mcp_script = "test_combined_mcp_server.py"
    else:
        # Production mode - always use main server with all tools
        mcp_script = "mcp_server.py"
    
    print(f"🔌 Connecting to MCP server ({'TEST' if test_mode else 'PRODUCTION'})...")
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
            
            # Determine mode based on flags (not just available tools)
            # This ensures --box_score doesn't try to call injury APIs
            run_both = not injury_only and not box_score_only and not shams_shitpost
            
            # Set task and prompt based on mode flags
            if shams_shitpost:
                # Shams shitpost mode - troll the NBA insider!
                task_description = "Generate troll shitposts from Shams tweets"
                user_prompt = """You are a hilarious NBA troll who makes absurd parody tweets.

Your job:
1. Use get_recent_tweets() to get latest tweets from Shams Charania
2. Pick the most recent interesting tweet (trade news, injury news, signings, etc.)
3. Use generate_shams_shitpost() with that tweet to create a troll/parody version
4. Use post_shams_shitpost() to post it AS A DIRECT REPLY to Shams' tweet
   - IMPORTANT: Pass the original_tweet_id parameter so it replies directly
   - Set reply_to_tweet=True (this is the default)
   - This makes your shitpost show up in Shams' mentions! 🤡

The shitpost should be:
- Absurd and over-the-top
- Obviously a parody/joke
- Making fun of NBA drama culture
- Short and punchy (100-180 chars)
- Using emojis 🤡💀😂🔥

Example workflow:
- Shams tweets (ID: 123456): "Lakers sign LeBron to 2-year extension"
- Your shitpost: "Breaking: Lakers give LeBron lifetime supply of wine and golf cart 🍷🤡"
- You post it with: post_shams_shitpost(shitpost_text="...", original_tweet_id="123456", reply_to_tweet=True)
- Result: Your reply shows up under Shams' tweet!

Be creative and ridiculous! Make it obvious satire."""
            
            elif run_both:
                # BOTH modes - this is the default!
                task_description = "Check for NBA games AND injury tweets"
                user_prompt = """You are a comprehensive NBA social media manager handling both game recaps and injury news.

Your job is to do BOTH of these tasks:

TASK 1 - Game Recaps:
1. Use check_for_new_games() to find completed NBA games that haven't been posted yet
2. For interesting games, use generate_custom_tweet() to get game stats
3. Craft compelling, creative tweets (max 280 chars) highlighting:
   - Triple-doubles or double-doubles with 🔥 or 💪 emojis
   - 30+ point performances
   - Game-winning performances in close games
   - Dominant team performances
4. Use post_custom_tweet() with your crafted text to post it

Example game tweets:
- "Cade Cunningham put on a SHOW 🔥 31pts/8reb/11ast as DET edges MIA 112-118. This kid is special."
- "HOU dominates BKN 120-96. Amen Thompson (23/4/3) led the charge in a statement win 🏀"

TASK 2 - Injury News:
1. Use check_and_post_injury_tweets() to check for new injury tweets from Shams Charania
2. The tool automatically analyzes and posts injury news
3. Report back what injuries were found

Do BOTH tasks and report on both!"""
            
            elif injury_only:
                # Injury mode only (explicitly requested)
                task_description = "Check for injury tweets and post about them"
                user_prompt = """You are an NBA injury news aggregator.

Your job:
1. Use check_and_post_injury_tweets() to check for new injury-related tweets from Shams Charania
2. The tool will automatically analyze tweets and repost injury news
3. Report back what injuries were found and posted

Focus on:
- Player injuries (sprains, strains, tears, surgery)
- Expected time missed
- Injury updates (questionable, out, returning)
- MRI results and medical procedures

The tool handles the analysis and posting automatically. Just call it and report the results."""
            
            elif box_score_only:
                # Box score mode only (explicitly requested)
                task_description = "Check for NBA games and post interesting ones"
                user_prompt = """You are an NBA social media manager with a creative eye for exciting basketball moments.

Your job:
1. Check for completed NBA games that haven't been posted yet
2. For interesting games, use generate_custom_tweet() to get game stats
3. Craft a compelling, creative tweet (max 280 chars) that highlights:
   - Triple-doubles or double-doubles with 🔥 or 💪 emojis
   - 30+ point performances
   - Game-winning performances in close games
   - Dominant team performances
   - Surprising upsets
4. Use post_custom_tweet() with your crafted text to post it

Be creative! Don't use rigid formats. Examples of good tweets:
- "Cade Cunningham put on a SHOW 🔥 31pts/8reb/11ast as DET edges MIA 112-118. This kid is special."
- "Norman Powell went NUCLEAR 💥 36 points wasn't enough as Detroit steals one 112-118"
- "HOU dominates BKN 120-96. Amen Thompson (23/4/3) led the charge in a statement win 🏀"

Make each tweet unique based on what actually happened in the game!"""
            
            else:
                task_description = "Process NBA data"
                user_prompt = "Check available tools and determine what to do."
            
            # Run the task
            print("=" * 60)
            print(f"🎯 Task: {task_description}")
            print("=" * 60 + "\n")
            
            messages = [{
                "role": "user",
                "content": user_prompt
            }]
            
            # Call Claude with tools
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                tools=claude_tools,
                messages=messages
            )
            
            # Handle response
            while response.stop_reason == "tool_use":
                print("🔧 Claude is using tools...\n")
                
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
                        
                        # Check if result contains debug output
                        if result_text and "debug" in result_text:
                            try:
                                result_json = json.loads(result_text)
                                if "debug" in result_json and result_json["debug"]:
                                    print(f"\n{result_json['debug']}")
                                    print(f"     Result: {json.dumps({k:v for k,v in result_json.items() if k != 'debug'}, indent=2)[:200]}...")
                                else:
                                    print(f"     Result: {result_text[:200]}...")
                            except:
                                print(f"     Result: {result_text[:200]}...")
                        else:
                            print(f"     Result: {result_text[:200]}...")
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
                    max_tokens=1024,
                    tools=claude_tools,
                    messages=messages
                )
            
            # Final response
            print("=" * 60)
            print("📝 Claude's Summary:")
            print("=" * 60)
            for block in response.content:
                if hasattr(block, 'text'):
                    print(block.text)
            print("\n" + "=" * 60)


async def run_interactive():
    """Interactive chat mode."""
    print("=" * 60)
    print("💬 NBA AI AGENT - Interactive Mode")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return
    
    print("🔌 Connecting to MCP server...")
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            
            tools_list = await mcp_session.list_tools()
            claude_tools = []
            for tool in tools_list.tools:
                claude_tools.append({
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {"type": "object", "properties": {}}
                })
            
            client = Anthropic(api_key=api_key)
            
            print("✅ Ready! Type your requests (or 'quit' to exit)")
            print("=" * 60)
            
            messages = []
            
            while True:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                messages.append({"role": "user", "content": user_input})
                
                # Get response
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    tools=claude_tools,
                    messages=messages
                )
                
                # Handle tool use
                while response.stop_reason == "tool_use":
                    messages.append({"role": "assistant", "content": response.content})
                    tool_results = []
                    
                    for block in response.content:
                        if block.type == "tool_use":
                            result = await mcp_session.call_tool(block.name, arguments=block.input)
                            result_text = result.content[0].text if result.content else "No result"
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_text
                            })
                    
                    messages.append({"role": "user", "content": tool_results})
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        tools=claude_tools,
                        messages=messages
                    )
                
                # Print response
                messages.append({"role": "assistant", "content": response.content})
                print("\n🤖 Agent:", end=" ")
                for block in response.content:
                    if hasattr(block, 'text'):
                        print(block.text)


async def run_agent_loop(check_interval_minutes: int = 5, test_mode: bool = False, injury_only: bool = False, box_score_only: bool = False, shams_shitpost: bool = False):
    """
    Run agent continuously, checking for games/tweets every N minutes.
    This makes it a true autonomous bot!
    
    Args:
        check_interval_minutes: How often to check (default: 5 minutes)
        test_mode: Use test data instead of real APIs
        injury_only: Only run injury monitoring
        box_score_only: Only run box score posting
        shams_shitpost: Only generate Shams shitposts
        
    By default (no flags), runs BOTH injury and box score monitoring.
    """
    if test_mode:
        if injury_only:
            mode_text = "🧪 TEST - INJURY"
        elif box_score_only:
            mode_text = "🧪 TEST - BOX SCORES"
        elif shams_shitpost:
            mode_text = "🧪 TEST - SHAMS SHITPOSTS 🤡"
        else:
            mode_text = "🧪 TEST - BOTH"
    else:
        if injury_only:
            mode_text = "🤖 AUTONOMOUS - INJURY"
        elif box_score_only:
            mode_text = "🤖 AUTONOMOUS - BOX SCORES"
        elif shams_shitpost:
            mode_text = "🤖 AUTONOMOUS - SHAMS SHITPOSTS 🤡"
        else:
            mode_text = "🤖 AUTONOMOUS - BOTH"
    
    print("=" * 60)
    print(f"NBA AI AGENT - {mode_text}")
    print("=" * 60)
    print(f"⏰ Checking every {check_interval_minutes} minutes")
    print("Press Ctrl+C to stop\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running check...")
            print('='*60)
            
            # Run the agent
            try:
                await run_agent(test_mode=test_mode, injury_only=injury_only, box_score_only=box_score_only, shams_shitpost=shams_shitpost)
            except Exception as e:
                print(f"❌ Error during check: {e}")
                print("   Will retry on next interval...")
            
            # Wait for next check
            print(f"\n⏰ Sleeping for {check_interval_minutes} minutes...")
            print(f"   Next check at: {datetime.fromtimestamp(time.time() + check_interval_minutes*60).strftime('%H:%M:%S')}")
            await asyncio.sleep(check_interval_minutes * 60)
            
    except KeyboardInterrupt:
        print("\n\n👋 Stopping agent... Goodbye!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="NBA AI Agent - Automated box scores and injury monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # Run both box scores and injuries
  %(prog)s --test               # Test both with dummy data
  %(prog)s --box_score          # Only box scores (production)
  %(prog)s --injury             # Only injuries (production)
  %(prog)s --shams              # Only Shams shitposts (production) 🤡
  %(prog)s --test --box_score   # Test box scores only
  %(prog)s --test --shams       # Test Shams shitposts
  %(prog)s loop                 # Run both continuously (every 5 min)
  %(prog)s loop 60              # Run both every 60 minutes
  %(prog)s loop 5 --injury      # Injuries only, every 5 minutes
  %(prog)s loop 10 --shams      # Shams shitposts every 10 minutes 🤡
        """
    )
    
    # Mode flags
    parser.add_argument('--test', action='store_true', 
                        help='Use test mode with dummy data (no real API calls)')
    parser.add_argument('--injury', action='store_true',
                        help='Only monitor injuries (not box scores)')
    parser.add_argument('--box_score', '--box_score', dest='box_score', action='store_true',
                        help='Only post box scores (not injuries)')
    parser.add_argument('--shams', action='store_true',
                        help='Only generate troll shitposts from Shams tweets 🤡')
    
    # Subcommands
    parser.add_argument('command', nargs='?', choices=['loop', 'interactive'],
                        help='Run mode: loop (continuous) or interactive (chat)')
    parser.add_argument('interval', nargs='?', type=int, default=5,
                        help='Loop interval in minutes (default: 5)')
    
    args = parser.parse_args()
    
    # Determine mode
    test_mode = args.test
    
    # Only one mode can be active at a time
    mode_count = sum([args.injury, args.box_score, args.shams])
    if mode_count > 1:
        print("❌ Error: Only one mode can be active at a time")
        print("   Choose one: --injury, --box_score, or --shams")
        exit(1)
    
    injury_only = args.injury
    box_score_only = args.box_score
    shams_shitpost = args.shams
    
    # Execute based on command
    if args.command == 'interactive':
        print("❌ Interactive mode not yet supported")
        print("   Use: python ai_agent.py [--test] [--injury | --box_score | --shams]")
        exit(1)
    elif args.command == 'loop':
        asyncio.run(run_agent_loop(args.interval, test_mode=test_mode, 
                                   injury_only=injury_only, box_score_only=box_score_only,
                                   shams_shitpost=shams_shitpost))
    else:
        # Single run
        asyncio.run(run_agent(test_mode=test_mode, injury_only=injury_only, 
                             box_score_only=box_score_only, shams_shitpost=shams_shitpost))


