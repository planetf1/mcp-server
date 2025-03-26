"""
A simple echo tool that returns the input text.
Useful for testing and debugging.
"""
from mcp_instance import mcp

@mcp.tool()
async def echo(text: str) -> str:
    """
    Echo back the input text exactly as provided.
    
    Args:
        text: The text to echo back
        
    Returns:
        The exact same text that was provided as input
    """
    return text
