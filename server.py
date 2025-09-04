# server.py
import asyncio
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("example-server")

# Simple tool that greets a user
@mcp.tool()
def say_hello(name: str) -> str:
    """
    Greets the user by name.
    
    Args:
        name: User's name as a string
    Returns:
        A greeting message
    """
    return f"Hello, {name}! Welcome to the MCP server."

# Another example tool: add two numbers
@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """
    Adds two numbers.
    
    Args:
        a: first number
        b: second number
    Returns:
        Sum of a and b
    """
    return a + b

# Run the server over stdio (compatible with your client.py)
if __name__ == "__main__":
    mcp.run(transport='stdio')
