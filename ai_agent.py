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


async def run_agent():
    """Run AI agent with Claude + MCP."""
    print("=" * 60)
    print("🤖 NBA AI AGENT")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        print("   Set it: export ANTHROPIC_API_KEY=your_key_here")
        return
    
    print("✅ API key found")
    
    # Connect to MCP server
    print("🔌 Connecting to MCP server...")
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
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
            
            # Run the task
            print("=" * 60)
            print("🎯 Task: Check for NBA games and post interesting ones")
            print("=" * 60 + "\n")
            
            messages = [{
                "role": "user",
                "content": """You are an NBA social media manager with a creative eye for exciting basketball moments.

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


async def run_agent_loop(check_interval_minutes: int = 5):
    """
    Run agent continuously, checking for games every N minutes.
    This makes it a true autonomous bot!
    
    Args:
        check_interval_minutes: How often to check (default: 5 minutes)
    """
    print("=" * 60)
    print("🤖 NBA AI AGENT - AUTONOMOUS MODE")
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
                await run_agent()
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
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            asyncio.run(run_interactive())
        elif sys.argv[1] == "loop":
            # Continuous mode with optional interval
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            asyncio.run(run_agent_loop(interval))
        else:
            print("Usage:")
            print("  python ai_agent.py           # Run once")
            print("  python ai_agent.py loop [N]  # Run every N minutes (default: 5)")
            print("  python ai_agent.py interactive  # Interactive chat mode")
    else:
        asyncio.run(run_agent())


