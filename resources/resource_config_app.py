from mcp_instance import mcp

@mcp.resource("config://app")
def get_config() -> str:
    """Static configuration data"""
    return "App configuration here"
