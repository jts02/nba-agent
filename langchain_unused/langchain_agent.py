#!/usr/bin/env python3
"""
LangChain AI Agent - Uses MCP server to autonomously manage NBA posts.

This is the REAL AI agent that can reason about games and decide what to post.
"""
import asyncio
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters import create_mcp_client_tools


class MCPTools:
    """Wrapper to convert MCP tools into LangChain tools."""
    
    def __init__(self, session: ClientSession):
        self.session = session
        self.tools = []
        
    async def initialize(self):
        """Discover tools from MCP server and wrap them."""
        mcp_tools = await self.session.list_tools()
        
        for mcp_tool in mcp_tools.tools:
            # Create a LangChain tool for each MCP tool
            langchain_tool = self._create_langchain_tool(mcp_tool)
            self.tools.append(langchain_tool)
    
    def _create_langchain_tool(self, mcp_tool):
        """Convert an MCP tool to a LangChain tool."""
        tool_name = mcp_tool.name
        tool_description = mcp_tool.description or "No description"
        
        @tool(name=tool_name, description=tool_description)
        async def mcp_tool_wrapper(**kwargs) -> str:
            """Dynamically created tool wrapper."""
            result = await self.session.call_tool(tool_name, arguments=kwargs)
            return result.content[0].text
        
        return mcp_tool_wrapper


async def run_agent():
    """Run the AI agent with MCP tools."""
    print("=" * 60)
    print("🤖 NBA AI AGENT - Starting Up")
    print("=" * 60)
    
    # Connect to MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to MCP server")
            
            # Wrap MCP tools for LangChain
            mcp_tools = MCPTools(session)
            await mcp_tools.initialize()
            print(f"✅ Loaded {len(mcp_tools.tools)} tools")
            
            # Initialize Claude
            llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            
            # Create agent prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an NBA social media manager. Your job is to:
                
1. Check for completed NBA games
2. Determine if any haven't been posted to Twitter yet
3. Post interesting games with notable performances
4. Avoid duplicate posts

Be concise and professional. Focus on games with:
- Triple-doubles or double-doubles
- 30+ point performances
- Close games (within 5 points)
- Notable statistical achievements

You have access to tools to check games, format tweets, and post to Twitter."""),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            # Create agent
            agent = create_tool_calling_agent(llm, mcp_tools.tools, prompt)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=mcp_tools.tools,
                verbose=True,
                max_iterations=10
            )
            
            print("\n" + "=" * 60)
            print("🤖 Agent Ready! Starting autonomous operation...")
            print("=" * 60)
            
            # Run agent with task
            task = """
            Check for completed NBA games today. For any games that haven't been posted yet:
            1. Review the box score
            2. If there are notable performances (30+ points, triple-doubles, double-doubles), post it
            3. Report what you did
            """
            
            result = await agent_executor.ainvoke({"input": task})
            
            print("\n" + "=" * 60)
            print("🎯 Agent Result:")
            print("=" * 60)
            print(result["output"])


async def run_interactive_agent():
    """Run the agent in interactive mode - you can chat with it."""
    print("=" * 60)
    print("💬 NBA AI AGENT - Interactive Mode")
    print("=" * 60)
    
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            mcp_tools = MCPTools(session)
            await mcp_tools.initialize()
            
            llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an NBA social media manager with access to NBA data and Twitter posting.
                You can check games, view stats, and post to Twitter. Be helpful and conversational."""),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            agent = create_tool_calling_agent(llm, mcp_tools.tools, prompt)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=mcp_tools.tools,
                verbose=True
            )
            
            print("\n✅ Agent ready! Type your requests (or 'quit' to exit)")
            print("=" * 60)
            
            while True:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                result = await agent_executor.ainvoke({"input": user_input})
                print(f"\n🤖 Agent: {result['output']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # Run in interactive mode: python langchain_agent.py interactive
        asyncio.run(run_interactive_agent())
    else:
        # Run autonomous mode: python langchain_agent.py
        asyncio.run(run_agent())

