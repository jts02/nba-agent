#!/usr/bin/env python3
"""
Simple LangChain AI Agent - Uses MCP server to manage NBA posts.

This uses langchain_mcp_adapters for easy integration.
"""
import asyncio
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters import create_mcp_client_tools

# Load environment variables
load_dotenv()


async def run_agent_simple():
    """Run AI agent with simple prompts."""
    print("=" * 60)
    print("🤖 NBA AI AGENT - Starting")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("   Set it with: export ANTHROPIC_API_KEY=your_key_here")
        return
    
    print("✅ API key found")
    
    # Create MCP tools from your server
    print("🔌 Connecting to MCP server...")
    tools = await create_mcp_client_tools(
        command="python",
        args=["mcp_server.py"]
    )
    print(f"✅ Loaded {len(tools)} tools from MCP server")
    
    # Show available tools
    print("\n📋 Available tools:")
    for tool in tools:
        print(f"   - {tool.name}")
    
    # Initialize Claude with tools
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=api_key
    )
    llm_with_tools = llm.bind_tools(tools)
    
    print("\n" + "=" * 60)
    print("🎯 Running Task: Check and post NBA games")
    print("=" * 60)
    
    # Create prompt
    prompt = """You are an NBA social media manager. 

Task: Check if there are any completed NBA games today that haven't been posted yet.
If there are, review their box scores and post games that have notable performances like:
- 30+ point games
- Triple-doubles or double-doubles
- Close games (within 5 points)

Be concise and tell me what you found and what you did."""
    
    # Run the agent
    messages = [HumanMessage(content=prompt)]
    
    print("\n🤖 Claude is thinking...")
    response = await llm_with_tools.ainvoke(messages)
    
    print("\n" + "=" * 60)
    print("📝 Claude's Response:")
    print("=" * 60)
    print(response.content)
    
    # If Claude wants to use tools, handle that
    if response.tool_calls:
        print(f"\n🔧 Claude wants to use {len(response.tool_calls)} tool(s)")
        
        for tool_call in response.tool_calls:
            print(f"   Calling: {tool_call['name']}")
            
            # Find and execute the tool
            tool = next((t for t in tools if t.name == tool_call['name']), None)
            if tool:
                result = await tool.ainvoke(tool_call['args'])
                print(f"   Result: {result}")
    
    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)


async def run_interactive():
    """Run in interactive chat mode."""
    print("=" * 60)
    print("💬 NBA AI AGENT - Interactive Mode")
    print("=" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        return
    
    print("🔌 Connecting to MCP server...")
    tools = await create_mcp_client_tools(
        command="python",
        args=["mcp_server.py"]
    )
    print(f"✅ Loaded {len(tools)} tools")
    
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=api_key
    )
    llm_with_tools = llm.bind_tools(tools)
    
    print("\n✅ Ready! Type your requests (or 'quit' to exit)")
    print("=" * 60)
    
    conversation_history = []
    
    while True:
        user_input = input("\n💬 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        # Add user message to history
        conversation_history.append(HumanMessage(content=user_input))
        
        # Get Claude's response
        response = await llm_with_tools.ainvoke(conversation_history)
        
        # Handle tool calls if any
        if response.tool_calls:
            print(f"\n🔧 Using {len(response.tool_calls)} tool(s)...")
            
            tool_results = []
            for tool_call in response.tool_calls:
                print(f"   • {tool_call['name']}")
                tool = next((t for t in tools if t.name == tool_call['name']), None)
                if tool:
                    result = await tool.ainvoke(tool_call['args'])
                    tool_results.append(result)
            
            # Get final response with tool results
            conversation_history.append(response)
            # In a real implementation, you'd add tool results to history
            final_response = await llm.ainvoke(conversation_history)
            print(f"\n🤖 Agent: {final_response.content}")
            conversation_history.append(final_response)
        else:
            print(f"\n🤖 Agent: {response.content}")
            conversation_history.append(response)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(run_interactive())
    else:
        asyncio.run(run_agent_simple())

