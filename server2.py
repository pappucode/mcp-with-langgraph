# server.py
from mcp.server.fastmcp import FastMCP
import logging
import sys

# send logs to stderr so stdio remains clean for MCP messages
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

mcp = FastMCP("mini-book-server")

@mcp.tool()
async def lookup_book(title: str) -> str:
    """
    Return a short description for a few books from a tiny local catalog.
    This demonstrates a simple tool a server exposes.
    """
    catalog = {
        "1984": "1984 — George Orwell. Dystopia about surveillance and totalitarianism.",
        "the hobbit": "The Hobbit — J.R.R. Tolkien. Prequel to LOTR; Bilbo's adventure.",
        "learn python": "Learn Python — A short guide to Python basics (example entry)."
    }
    return catalog.get(title.lower(), f"No entry found for '{title}'. Try another title.")

if __name__ == "__main__":
    # run with stdio so a client can spawn this script as subprocess
    # IMPORTANT: don't print() to stdout in stdio servers (use logging to stderr).
    mcp.run(transport="stdio")
