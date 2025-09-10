# client.py
import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Optional
from dotenv import load_dotenv

# mcp client bits
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# langchain / ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.schema.messages import SystemMessage, HumanMessage

load_dotenv()  # loads OPENAI_API_KEY from .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in your .env before running.")

class MCPChatClient:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        # ChatOpenAI object (sync invoke; we'll call it via asyncio.to_thread)
        self.chat = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name=model_name, temperature=0)
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None
        self.stdio = None
        self.write = None

    async def connect_to_server(self, server_script_path: str):
        """Spawn/connect to a local server script using the stdio transport."""
        server_params = StdioServerParameters(command="python", args=[server_script_path], env=None)

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))

        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        tools_resp = await self.session.list_tools()
        print("Connected — available tools:", [t.name for t in tools_resp.tools])

    async def close(self):
        await self.exit_stack.aclose()

    async def ask(self, user_text: str) -> str:
        """Simple loop: ask model; if it requests a tool (via JSON), call it and pass result back."""
        # list server tools (short descriptions)
        tools_resp = await self.session.list_tools()
        tools_text = "\n".join([f"- {t.name}: {t.description or ''}" for t in tools_resp.tools])

        system = SystemMessage(
            content=(
                "You are a helpful assistant. The server provides these tools:\n"
                f"{tools_text}\n\n"
                "If you want to call a tool, reply with ONLY valid JSON like:\n"
                '{"tool_name": "lookup_book", "tool_args": {"title": "1984"}}\n'
                "Otherwise reply with JSON: {\"text\": \"your final assistant text here\"}."
            )
        )
        human = HumanMessage(content=user_text)

        # call ChatOpenAI synchronously inside a thread so we can await it
        model_response = await asyncio.to_thread(self.chat.invoke, [system, human])
        text = model_response.content.strip()

        # try to parse JSON command
        try:
            parsed = json.loads(text)
        except Exception:
            # model didn't follow JSON rule — return raw text
            return text

        # if model asked to call a tool:
        if parsed.get("tool_name"):
            tool_name = parsed["tool_name"]
            tool_args = parsed.get("tool_args", {})
            print(f"Model asked to call tool {tool_name} with args {tool_args}")

            # call the tool via MCP session
            tool_result = await self.session.call_tool(tool_name, tool_args)
            # tool_result is an MCP response object; use its content if available
            # Extract plain text from tool_result.content
            if hasattr(tool_result, "content"):
                parts = []
                for c in tool_result.content:
                    if hasattr(c, "text"):
                        parts.append(c.text)
                    else:
                        parts.append(str(c))
                tool_content = "\n".join(parts)
            else:
                tool_content = str(tool_result)

            # create follow-up messages including the tool result and ask model to finalize
            followup_human = HumanMessage(
                content=json.dumps({
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "content": tool_content
                })
            )
            final_resp = await asyncio.to_thread(self.chat.invoke, [system, human, followup_human])
            return final_resp.content

        # else return assistant text
        return parsed.get("text", text)


async def main():
    client = MCPChatClient()
    await client.connect_to_server("server2.py")  # client will spawn server.py as a subprocess (stdio)
    try:
        while True:
            q = input("\nYou> ")
            if not q.strip():
                continue
            if q.strip().lower() in ("exit", "quit"):
                break
            out = await client.ask(q)
            print("\nAssistant>", out)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
