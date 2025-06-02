#!/usr/bin/env python3
import argparse
import logging
import os
import importlib.util
import inspect
import sys
import asyncio
from typing import List, Dict, Any, Optional, Callable, Tuple
from mcp.server.fastmcp import FastMCP

# Logger for this application
logger = logging.getLogger(__name__)
mcp_sdk_logger = logging.getLogger("mcp")


# --- Built-in Tools ---
def echo(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    Echoes back the invocation parameters.
    """
    logger.debug(f"Echo tool called with args: {args}, kwargs: {kwargs}")
    return {"args": args, "kwargs": kwargs}


def health() -> str:
    """
    Reports the server's health status.
    """
    logger.debug("Health tool called.")
    return "ready"


def setup_logging(log_file: Optional[str] = None) -> None:
    """
    Configures logging for the application and MCP SDK.
    """
    root_logger = logging.getLogger()
    # Clear any existing handlers from root logger to avoid duplication
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Also clear handlers from our specific loggers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    for handler in mcp_sdk_logger.handlers[:]:
        mcp_sdk_logger.removeHandler(handler)

    # Prevent our loggers from propagating to the root logger if we are configuring them directly
    logger.propagate = False
    mcp_sdk_logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(message)s"
    )  # Simple format for console startup messages
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)  # Console always gets INFO for startup messages

    logger.addHandler(console_handler)  # App's logger gets console handler
    logger.setLevel(logging.INFO)  # Default app level

    if log_file:
        logger.info(f"Detailed logging enabled. Outputting DEBUG logs to: {log_file}")
        logger.info("INFO level messages will also be printed to the console.")

        file_handler = logging.FileHandler(log_file, mode="w")
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets everything

        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)  # App logger to DEBUG if file logging

        mcp_sdk_logger.addHandler(file_handler)  # MCP SDK also logs to the file
        mcp_sdk_logger.setLevel(logging.DEBUG)  # Full details for MCP SDK
    else:
        # If no log file, MCP SDK logs warnings and above to console via its own handler if needed
        # or we can add our console handler to it for consistency.
        # For simplicity, let's keep MCP SDK quieter on console if no file log.
        mcp_sdk_logger.setLevel(logging.WARNING)
        # If you want MCP INFO/DEBUG on console when no log file, add console_handler to mcp_sdk_logger here.

ToolFunctionType = Callable[..., Any]

def load_tool_from_file(file_path: str) -> Tuple[Optional[ToolFunctionType], Optional[str]]:
    """
    Loads a tool from a Python file.
    Validates that the file contains exactly one function definition (not imported ones).
    """
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if not spec or not spec.loader:
        logger.error(f"Could not create module spec for {file_path}")
        return None, None

    try:
        module = importlib.util.module_from_spec(spec)
    except Exception as e: # Should not happen if spec is valid, but good for robustness
        logger.error(f"Could not create module from spec for {file_path}: {e}", exc_info=True)
        return None, None

    tool_dir = os.path.dirname(os.path.abspath(file_path))
    path_prepended = False
    if tool_dir not in sys.path:
        sys.path.insert(0, tool_dir)
        path_prepended = True

    try:
        if spec.loader: # Ensure loader is not None
            spec.loader.exec_module(module)
        else: # Should be caught by the spec check above, but defensive
            logger.error(f"Module spec loader is None for {file_path}")
            return None, None
    except Exception as e:
        logger.error(f"Error executing module {module_name} from {file_path}: {e}", exc_info=True)
        return None, None
    finally:
        if path_prepended:
            if sys.path and sys.path[0] == tool_dir:
                sys.path.pop(0)

    functions: List[ToolFunctionType] = []
    for name, member in inspect.getmembers(module):
        if inspect.isfunction(member) and member.__module__ == module_name:
            # Check if the function is defined in this module, not imported.
            functions.append(member)

    if len(functions) == 0:
        logger.warning(
            f"No function found in {file_path} defined directly in the module. Skipping."
        )
        return None, None
    if len(functions) > 1:
        logger.warning(
            f"Multiple functions ({[f.__name__ for f in functions]}) found in {file_path} defined directly in the module. "
            "Only one function definition per tool file is allowed. Skipping."
        )
        return None, None

    tool_function = functions[0]
    logger.debug(
        f"Successfully loaded tool '{tool_function.__name__}' from module '{module_name}' ({file_path})"
    )
    return tool_function, module_name


def discover_tools(tools_paths_list: List[str]) -> Dict[str, Tuple[ToolFunctionType, str]]:
    """
    Discovers tools from the given list of paths (each can be a file or directory).
    """
    discovered_tools: Dict[str, Tuple[ToolFunctionType, str]] = {}
    if not tools_paths_list: # Handle empty list if no paths are provided
        return discovered_tools

    for tools_path_str_item in tools_paths_list:
        tools_path = os.path.abspath(tools_path_str_item)

        if os.path.isfile(tools_path):
            if tools_path.endswith(".py"):
                tool_func, module_name = load_tool_from_file(tools_path)
                if tool_func:
                    discovered_tools[tool_func.__name__] = (tool_func, module_name)
            else:
                logger.warning(f"Provided tool path {tools_path} is a file but not a .py file. Skipping.")
        elif os.path.isdir(tools_path):
            logger.info(f"Searching for tools in directory: {tools_path}")
            for filename in os.listdir(tools_path):
                if filename.endswith(".py") and not filename.startswith("_"): # Ignore __init__.py etc.
                    file_path = os.path.join(tools_path, filename)
                    tool_func, module_name = load_tool_from_file(file_path)
                    if tool_func:
                        discovered_tools[tool_func.__name__] = (tool_func, module_name)
        else:
            logger.warning(f"Tools path {tools_path_str_item} (resolved to {tools_path}) is not a valid file or directory. Skipping custom tool loading for this entry.")
    return discovered_tools


async def run_server_transport(mcp_instance: FastMCP, transport_type: str, port: int) -> None:
    # The mcp_instance.run() method is blocking.
    # We run it in a separate thread to keep the asyncio event loop free.
    def _run_blocking() -> None:
        if transport_type == "stdio":
            logger.info("Starting MCP server with stdio transport.")
            mcp_instance.run(transport="stdio")
        elif transport_type == "sse":
            host = "0.0.0.0" # Ensure server is accessible externally
            # Default SSE mount path for FastMCP.run is typically /sse
            logger.info(f"Starting MCP server with SSE transport on http://{host}:{port}/sse")
            mcp_instance.run(transport="sse", port=port, host=host)
        else:
            # This will be raised in the thread, and caught by the await asyncio.to_thread
            logger.error(f"Unsupported transport type: {transport_type}")
            raise ValueError(f"Unsupported transport type: {transport_type}")

    try:
        await asyncio.to_thread(_run_blocking)
    except asyncio.CancelledError:
        # This occurs if the task created by asyncio.to_thread is cancelled.
        # The thread running _run_blocking may or may not terminate immediately
        # depending on whether _run_blocking is itself interruptible.
        logger.debug("run_server_transport: asyncio.to_thread task was cancelled.")
        raise # Propagate CancelledError to amain
    except ValueError: # For unsupported transport type from _run_blocking
        # Let amain's general exception handler deal with this after logging.
        # sys.exit(1) here would only exit the thread.
        raise # Re-raise the ValueError to be caught by amain


async def amain() -> None:
    # Add these lines for diagnostics
    logger.debug(f"Executing with Python: {sys.executable}")
    logger.debug(f"Python sys.path: {sys.path}")
    parser = argparse.ArgumentParser(
        description="MCP Tool Server", formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "tools_paths", # Changed argument name to reflect it can be multiple
        nargs="*",     # Changed from "?" to "*" to accept zero or more arguments
        default=[],    # Default to an empty list if no paths are provided
        help="Paths to Python tool files or directories containing Python tool files.\n"
             "Example: ./my_tool.py ./my_other_tool.py ./tools_directory"
    )
    parser.add_argument(
        "--log",
        metavar="FILENAME",
        help="Enable detailed logging (DEBUG level for app and MCP SDK) to the specified file.\n"
        "Includes full details of tool calls and responses.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Communication transport to use (stdio or sse). Default: stdio",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to use for SSE transport. Default: 8080",
    )
    args = parser.parse_args()

    setup_logging(args.log)

    mcp_server_instance = FastMCP()
    registered_tools_info: List[str] = []

    # Register built-in tools
    mcp_server_instance.add_tool(echo)
    registered_tools_info.append(f"  - echo (from built-in)")
    logger.debug("Registered built-in tool: echo")

    mcp_server_instance.add_tool(health)
    registered_tools_info.append(f"  - health (from built-in)")
    logger.debug("Registered built-in tool: health")

    # Discover and register custom tools
    if args.tools_paths: # Check if the list of paths is not empty
        custom_tools = discover_tools(args.tools_paths) # Pass the list of paths
        for tool_name, (tool_func, module_name) in custom_tools.items():
            mcp_server_instance.add_tool(tool_func)
            registered_tools_info.append(f"  - {tool_name} (from {module_name})")
            logger.info(f"Registered custom tool: {tool_name} from module {module_name}")

    logger.info("MCP Server starting. Available tools:")
    for tool_info_line in registered_tools_info:
        logger.info(tool_info_line)  # This goes to console (INFO) and file (if --log)

    try:
        await run_server_transport(mcp_server_instance, args.transport, args.port)
    except asyncio.CancelledError:
        # This is the most common path for Ctrl+C when using asyncio.run(),
        # as asyncio.run() cancels the main coroutine.
        logger.info("MCP Server main task cancelled (Ctrl+C pressed). Shutting down...")
    except KeyboardInterrupt:
        # This might be caught if KeyboardInterrupt propagates from the thread
        # before asyncio.run() cancels amain.
        logger.info("MCP Server received KeyboardInterrupt. Shutting down...")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        # Removed sys.exit(1); asyncio.run() will handle process exit.

if __name__ == "__main__":
    asyncio.run(amain())
