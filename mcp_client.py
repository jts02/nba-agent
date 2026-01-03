#!/usr/bin/env python3
"""
MCP Client - For testing your MCP server locally.
This is NOT the AI agent - it's just for debugging.
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Test MCP server by calling its tools."""
    print("=" * 60)
    print("MCP CLIENT TEST - Connecting to MCP Server")
    print("=" * 60)
    
    # Connect to your MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            print("\n✅ Connected to MCP server!")
            
            # List available tools
            tools = await session.list_tools()
            print(f"\n📋 Available tools: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"   - {tool.name}: {tool.description}")
            
            # Test 1: Check for completed games
            print("\n" + "=" * 60)
            print("TEST 1: Getting completed games today")
            print("=" * 60)
            
            result = await session.call_tool("get_completed_games_today", arguments={})
            if result.content:
                print(result.content[0].text)
            else:
                print("⚠️  No content returned (probably no games today)")
            
            # Test 2: Check for new games (not yet posted)
            print("\n" + "=" * 60)
            print("TEST 2: Checking for new games to post")
            print("=" * 60)
            
            result = await session.call_tool("check_for_new_games", arguments={})
            if result.content:
                print(result.content[0].text)
            else:
                print("⚠️  No content returned")
            
            # Test 3: Get already posted games
            print("\n" + "=" * 60)
            print("TEST 3: Getting posted games history")
            print("=" * 60)
            
            result = await session.call_tool("get_posted_games", arguments={})
            if result.content:
                print(result.content[0].text)
            else:
                print("⚠️  No posted games yet")
            
            print("\n" + "=" * 60)
            print("✅ All tests completed!")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
