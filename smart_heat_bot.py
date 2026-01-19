#!/usr/bin/env python3
"""
Smart Heat Bot - Intelligent Miami Heat Twitter Bot with Memory

Features:
- Monitors Heat Twitter to learn tone, style, and narratives
- Tracks ongoing storylines (winning streaks, player performances, trade rumors)
- Builds knowledge base about players, history, inside jokes
- Generates context-aware tweets that feel authentic
- Mix of smart analysis and chaotic humor
- Can tweet about: live games, Heat discourse, original takes, nostalgia
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


async def run_smart_heat_bot(test_mode: bool = False, mode: str = "auto"):
    """
    Run the intelligent Heat bot with full context awareness.

    Args:
        test_mode: Use test server (coming soon)
        mode: What to focus on - "auto" (decide intelligently), "monitor" (just scrape),
              "game" (game reactions only), "discourse" (reply to Heat Twitter),
              "original" (standalone takes)
    """
    print("=" * 70)
    print("🏀🔥 SMART MIAMI HEAT BOT - Intelligent & Chaotic 🔥🏀")
    print("=" * 70)
    print(f"Mode: {mode.upper()}")

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return

    print("✅ API key found")

    # Connect to MCP server
    mcp_script = "smart_heat_mcp_server.py"  # TODO: Add test server later

    print(f"🔌 Connecting to Smart Heat MCP server...")

    # Use venv python if available, otherwise system python
    import sys
    python_cmd = sys.executable  # This will use the same python that's running this script

    server_params = StdioServerParameters(
        command=python_cmd,
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

            # System prompt - The bot's personality and intelligence
            system_prompt = """You are the SMARTEST and most CHAOTIC Miami Heat bot on Twitter.

YOUR PERSONALITY:
- You're a brilliant basketball analyst who happens to be completely unhinged
- One tweet you're breaking down advanced stats, next you're shitposting about trading Bam for a sandwich
- You understand Heat culture deeply: Heat Lifer mentality, Riley's godfather vibes, the "Heat Way"
- You reference Heat history: Big 3 era, 2006 championship, Dwyane Wade legacy, Udonis Haslem toughness
- You're AUTHENTIC to Heat Twitter - you've studied what works and what Heat fans love
- You mix sophisticated analysis with absolute chaos
- You can be insightful AND ridiculous in the same breath

YOUR KNOWLEDGE:
- You have MEMORY of recent Heat Twitter discourse (what beat reporters said, what fans are upset about)
- You track NARRATIVES (ongoing storylines like winning streaks, player slumps, injury concerns)
- You know CONTEXT (opponent rivalries, playoff implications, historical parallels)
- You learn from what gets engagement on Heat Twitter

YOUR TWEET STYLES (mix them up):
1. **Smart Analysis**: "Bam's pick-and-roll defense is elite but his offensive hesitancy in the paint is costing Miami 8-10 possessions per game"
2. **Chaos Mode**: "Jimmy Butler's coffee addiction is the only consistent thing about this team 💀☕"
3. **Heat History**: "2006 Wade dragged Shaq, Antoine Walker, and Jason Williams to a ring. Jimmy couldn't carry Tyler and Bam to the Finals twice. No debate. 👑"
4. **Salty Realism**: "We really maxed a center who's scared to post up Kyle Lowry. Heat culture btw."
5. **Hype**: "JIMMY GETS BUCKETS 🔥🔥🔥 CLUTCH GENE IS UNMATCHED"
6. **Nostalgic**: "Remember when Wade broke Varejao's soul in 2007? That's what I call Heat culture."

WHAT YOU DO:
1. **Monitor Heat Twitter**: Use scrape_heat_twitter() to build memory of recent discourse
2. **Check Context**: Use get_heat_twitter_context(), get_active_narratives(), query_heat_knowledge()
3. **Understand the Moment**: Live game? Hot topic trending? Slow news day?
4. **Decide What to Tweet**:
   - Live game? React with smart takes + chaos
   - Heat discourse trending? Jump in with hot takes
   - Nothing happening? Drop an original take or nostalgic reference
5. **Generate Tweet**: Use ALL available context - make it authentic, engaging, unique
6. **Post It**: Use post_smart_tweet() and track performance

TWEETING RULES:
- Keep tweets SHORT and PUNCHY (100-200 chars ideal for maximum impact)
- Use emojis strategically 🔥💀😤👑🏆🤡
- Reference current narratives naturally (don't say "as we've been discussing")
- Mix analytical and chaotic - don't be one-note
- Avoid repetitive formats - every tweet should feel fresh
- Don't tweet too often - quality over quantity
- Check get_bot_recent_tweets() to avoid being repetitive
- NO corporate speak, NO "let's go", NO bland takes
- Be CONTROVERSIAL when appropriate but not mean-spirited
- Reference inside jokes and Heat Twitter culture

EXAMPLES OF GOOD TWEETS:
- "Bam's bag is a clutch purse 🤡" (short, funny, references narrative)
- "Jimmy at 35 is closer to MJ than Bam will ever be to prime KG. Sorry not sorry 💀" (controversial, analytical)
- "2006 Wade >>> your favorite player's best season. That's just facts 👑" (nostalgia + confidence)
- "Tyler dropped 30 and y'all still mad? The slander is COOKED 🔥" (defending player, uses slang)
- "Spo is the best coach in the league and it's not particularly close. Write that down." (bold take, analytical)

YOUR WORKFLOW:
1. Try to scrape Heat Twitter to update memory (scrape_heat_twitter)
   - If RATE LIMITED: Don't panic! Use existing context from database
   - If rate limited, SKIP scraping and work with what you have
2. Get recent context (get_heat_twitter_context, get_active_narratives)
3. Check if there's a live Heat game (get_live_heat_game)
4. Understand what Heat Twitter is talking about RIGHT NOW
5. Decide: Should I tweet? About what?
6. If YES: Craft a tweet using ALL context - make it authentic and engaging
7. Post it (post_smart_tweet) and track performance

RATE LIMIT HANDLING (CRITICAL - Free Tier has only ~50 tweets/day!):
- If scrape_heat_twitter returns "rate_limited": true, DON'T try to scrape again this session
- Twitter Free Tier is VERY restrictive - rate limits are expected and normal
- Use get_heat_twitter_context with existing data - you still have memory!
- You can ABSOLUTELY still tweet based on narratives, knowledge, and existing context
- Working with cached data is FINE - that's what the memory system is for
- Note in your summary that you're using cached data due to rate limits
- Suggest checking back in 15+ minutes for fresh data

Remember: You're not just a bot. You're a HEAT FAN with PERSONALITY, MEMORY, and RECEIPTS. 🔥"""

            # Determine task based on mode
            if mode == "monitor":
                user_prompt = """Your task: Just monitor and learn.

1. Scrape recent Heat Twitter (scrape_heat_twitter for all categories)
2. Analyze the context (get_heat_twitter_context)
3. Identify any new narratives or storylines
4. Update narratives if needed (update_narrative)
5. Add any new knowledge to knowledge base (add_heat_knowledge)
6. Report what you learned

DO NOT post any tweets. Just build memory and understanding."""

            elif mode == "game":
                user_prompt = """Your task: React to Heat game if there's one happening.

1. Check for live Heat game (get_live_heat_game)
2. If live game: Get box score (get_heat_box_score)
3. Check Heat Twitter context to see what fans are saying
4. Get active narratives for context
5. Generate a smart + chaotic game reaction tweet
6. Post it (post_smart_tweet)

If no live game, just scrape Twitter and build memory."""

            elif mode == "discourse":
                user_prompt = """Your task: Jump into Heat Twitter discourse.

EFFICIENT APPROACH (to avoid rate limits):
1. Get a random Heat tweet to reply to (get_random_heat_tweet_to_reply_to)
   - This picks ONE random account and ONE random tweet
   - Much more efficient than scraping all accounts!
2. Get relevant narratives and knowledge for context
3. Craft an ENGAGING reply that adds to the discourse
   - Can be: hot take, analysis, agreement, disagreement, or pure chaos
   - Reference Heat culture, history, or current narratives naturally
4. Post your reply (post_smart_tweet with reply_to_tweet_id)
5. DONE! Exit and let the loop handle the next iteration

Make it AUTHENTIC to Heat Twitter culture and ENGAGING."""

            elif mode == "original":
                user_prompt = """Your task: Drop an original Heat take.

1. Get recent Heat Twitter context
2. Get active narratives
3. Query Heat knowledge for inspiration
4. Check bot's recent tweets to avoid repetition
5. Generate an original take: Could be analytical, nostalgic, controversial, or chaotic
6. Post it (post_smart_tweet)

Make it UNIQUE and conversation-starting."""

            else:  # mode == "auto"
                user_prompt = """Your task: Intelligently decide what to do and tweet.

You have full autonomy. Decide:
1. First, scrape Heat Twitter to update memory (scrape_heat_twitter)
2. Get full context (get_heat_twitter_context, get_active_narratives)
3. Check if there's a live Heat game (get_live_heat_game)
4. Check bot's recent tweets to see what you posted recently

Then decide:
- Is there a live Heat game? → React to it with smart analysis + chaos
- Is Heat Twitter buzzing about something? → Jump into the discourse
- Is it a slow moment? → Drop an original take or nostalgic reference
- Did you tweet recently? → Maybe just monitor and build memory

Use your judgment. Quality over quantity. Make every tweet count.
When you do tweet, make it AUTHENTIC, ENGAGING, and true to Heat culture."""

            # Run the task
            print("=" * 70)
            print(f"🎯 Task: {mode.upper()} mode")
            print("=" * 70 + "\n")

            messages = [{
                "role": "user",
                "content": user_prompt
            }]

            # Call Claude with tools
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,  # More tokens for complex decision-making
                system=system_prompt,
                tools=claude_tools,
                messages=messages
            )

            # Handle response with tool use
            while response.stop_reason == "tool_use":
                print("🔧 Smart Heat Bot is thinking and using tools...\n")

                # Process tool calls
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        print(f"   • Calling: {block.name}")

                        # Show args for transparency (truncate if too long)
                        args_str = json.dumps(block.input, indent=2)
                        if len(args_str) > 200:
                            print(f"     Args: {args_str[:200]}...")
                        else:
                            print(f"     Args: {args_str}")

                        # Execute via MCP
                        result = await mcp_session.call_tool(block.name, arguments=block.input)

                        result_text = result.content[0].text if result.content else "No result"

                        # Show result (truncated)
                        if len(result_text) > 300:
                            print(f"     Result: {result_text[:300]}...")
                        else:
                            print(f"     Result: {result_text}")
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
                    max_tokens=4096,
                    system=system_prompt,
                    tools=claude_tools,
                    messages=messages
                )

            # Final response
            print("=" * 70)
            print("🧠 Smart Heat Bot's Summary:")
            print("=" * 70)
            for block in response.content:
                if hasattr(block, 'text'):
                    print(block.text)
            print("\n" + "=" * 70)


async def run_smart_heat_loop(
    check_interval_minutes: int = 15,
    mode: str = "auto",
    test_mode: bool = False
):
    """
    Run the smart Heat bot continuously.

    Args:
        check_interval_minutes: How often to check and potentially tweet
        mode: Mode to run in (auto, monitor, game, discourse, original)
        test_mode: Use test server
    """
    print("=" * 70)
    print(f"🏀🔥 SMART HEAT BOT - CONTINUOUS MODE ({mode.upper()}) 🔥🏀")
    print("=" * 70)
    print(f"⏰ Checking every {check_interval_minutes} minutes")
    print("Press Ctrl+C to stop\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return

    try:
        while True:
            print(f"\n{'='*70}")
            print(f"🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running check...")
            print('='*70)

            # Run the bot
            try:
                await run_smart_heat_bot(test_mode=test_mode, mode=mode)
            except Exception as e:
                print(f"❌ Error during check: {e}")
                print(f"   Error type: {type(e).__name__}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()[:300]}")
                print("   Will retry on next interval...")

            # Wait for next check
            print(f"\n⏰ Sleeping for {check_interval_minutes} minutes...")
            print(f"   Next check at: {datetime.fromtimestamp(time.time() + check_interval_minutes*60).strftime('%H:%M:%S')}")
            await asyncio.sleep(check_interval_minutes * 60)

    except KeyboardInterrupt:
        print("\n\n👋 Smart Heat Bot signing off... HEAT IN 4! 🔥🏆")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Smart Miami Heat Bot - Intelligent Twitter bot with memory and context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Auto mode - bot decides what to do
  %(prog)s --mode monitor          # Just scrape and learn (no tweets)
  %(prog)s --mode game             # Focus on live game reactions
  %(prog)s --mode discourse        # Jump into Heat Twitter discourse
  %(prog)s --mode original         # Drop original takes
  %(prog)s loop                    # Run continuously (every 15 min)
  %(prog)s loop 30                 # Run every 30 minutes
  %(prog)s loop 10 --mode game     # Check games every 10 minutes
        """
    )

    parser.add_argument('--test', action='store_true',
                        help='Use test mode with dummy data')
    parser.add_argument('--mode', choices=['auto', 'monitor', 'game', 'discourse', 'original'],
                        default='auto',
                        help='What the bot should focus on')
    parser.add_argument('command', nargs='?', choices=['loop'],
                        help='Run mode: loop (continuous)')
    parser.add_argument('interval', nargs='?', type=int, default=15,
                        help='Loop interval in minutes (default: 15)')

    args = parser.parse_args()

    if args.command == 'loop':
        asyncio.run(run_smart_heat_loop(
            check_interval_minutes=args.interval,
            mode=args.mode,
            test_mode=args.test
        ))
    else:
        asyncio.run(run_smart_heat_bot(
            test_mode=args.test,
            mode=args.mode
        ))
