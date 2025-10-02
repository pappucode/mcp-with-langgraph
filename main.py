import random
from fastmcp import FastMCP

# Create a FastMCP server instance
mcp = FastMCP(name="Demo Server")


@mcp.tool
def roll_dice(n_dice: int = 1) -> list(int):
    """Roll n_dice 6-sided dice and return the results."""
    return []