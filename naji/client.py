import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv
load_dotenv()

async def main():
    try:
        client = MultiServerMCPClient(
            {
                "math": {
                    "command": "python",
                    "args": ["math-server.py"],
                    "transport": "stdio" 
                },
                "weather": {
                    "url": "http://localhost:8000/mcp",
                    "transport": "streamable_http"
                }
            }
        )

        tools = await client.get_tools()
        agent = create_react_agent("gpt-4o", tools=tools)

        math_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "What is (5+5)*10"}]}
        )
        print(math_response['messages'][-1].content)

        weather_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "What is the temperature in NY"}]}
        )
        print(weather_response['messages'][-1].content)

    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    asyncio.run( main())
