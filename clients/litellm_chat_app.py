#!/usr/bin/env python3
"""
Simple chat application that connects to Ollama models through LiteLLM
and provides tools via MCP protocol for enhanced capabilities.

Environment variables:
- OLLAMA_SERVER: Base URL for Ollama server (default: 'http://localhost:11434')
- OLLAMA_MODEL: Model to use with Ollama (default: 'granite3.2:latest')
- MCP_ENDPOINT: MCP server endpoint (default: 'localhost:3000')
- LOG_FILE: Path to log file (default: 'chat_interactions.log')
"""

import os
import sys
import json
import logging
import datetime
from typing import Dict, List, Any, Optional
import litellm
from litellm import completion
import httpx # For fetching MCP tools
from litellm.utils import get_secret
import colorama

# Initialize colorama for cross-platform colored terminal output
colorama.init()

# Enable parameter dropping for unsupported parameters
litellm.drop_params = True

# Configure logging to write only to file, not to console
LOG_FILE = os.environ.get("LOG_FILE", "chat_interactions.log")

# Create logger
logger = logging.getLogger("litellm_chat")
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(LOG_FILE, mode='a')
file_handler.setLevel(logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

# Prevent propagation to root logger (which might log to console)
logger.propagate = False

# Configuration via environment variables
OLLAMA_SERVER = os.environ.get("OLLAMA_SERVER", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "granite3.3:8b")
MCP_ENDPOINT = os.environ.get("MCP_ENDPOINT", "localhost:3001")

# Colors for better terminal experience
CYAN = colorama.Fore.CYAN
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
RED = colorama.Fore.RED
RESET = colorama.Fore.RESET

def setup_litellm() -> None:
    """Configure LiteLLM with Ollama and MCP."""
    # Use environment variable for logging instead of deprecated set_verbose
    os.environ["LITELLM_LOG"] = "INFO"

    # Setup MCP tools
    litellm.mcp_endpoint = f"http://{MCP_ENDPOINT}"

    # Define a compatible callback function that handles the LiteLLM callback signature
    def log_callback(**kwargs):
        try:
            # Extract relevant information from kwargs
            if "response_obj" in kwargs:
                response_obj = kwargs["response_obj"]
                request = kwargs.get("request", {})

                # Format for the log
                log_data = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "model": request.get("model", "unknown"),
                    "messages": request.get("messages", []),
                    "response": response_obj,
                }

                # Log detailed interaction
                logger.info(json.dumps(log_data, default=str))
        except Exception as e:
            logger.error(f"Error in logging callback: {str(e)}")

    # Register the callback
    litellm.callbacks = [log_callback]

    logger.info(f"LiteLLM configured with Ollama server: {OLLAMA_SERVER}, model: {OLLAMA_MODEL}")
    logger.info(f"MCP endpoint configured: {litellm.mcp_endpoint}")

def format_message(message: Dict[str, str]) -> str:
    """Format a chat message for display."""
    role = message.get("role", "unknown")
    content = message.get("content", "")

    if role == "user":
        return f"{CYAN}You: {content}{RESET}"
    elif role == "assistant":
        return f"{GREEN}Assistant: {content}{RESET}"
    elif role == "system":
        return f"{YELLOW}System: {content}{RESET}"
    else:
        return f"{role}: {content}"

def fetch_mcp_tools(mcp_api_base: str) -> Optional[List[Dict[str, str]]]:
    """Fetches available tools from the MCP server's OpenAPI schema."""
    tools_info = []
    openapi_url = f"{mcp_api_base}/openapi.json"
    try:
        logger.info(f"Fetching MCP tools from {openapi_url}")
        response = httpx.get(openapi_url, timeout=10.0)
        response.raise_for_status()  # Raise an exception for HTTP errors
        openapi_schema = response.json()

        paths = openapi_schema.get("paths", {})
        for path, path_item in paths.items():
            if path.startswith("/tool/") and path.endswith("/call") and "post" in path_item:
                operation = path_item["post"]
                # Extract tool name from path: /tool/{tool_name}/call
                tool_name_parts = path.split('/')
                if len(tool_name_parts) == 4: # ['', 'tool', tool_name, 'call']
                    tool_name = tool_name_parts[2]
                    description = operation.get("description", "No description available.")
                    tools_info.append({"name": tool_name, "description": description})
        
        if not tools_info:
            logger.warning(f"No MCP tools found in OpenAPI schema at {openapi_url}")
        else:
            logger.info(f"Found MCP tools: {tools_info}")
        return tools_info
    except httpx.RequestError as e:
        logger.error(f"Error fetching MCP tools from {openapi_url}: {e}")
        print(f"{RED}Error connecting to MCP server to fetch tools: {e}{RESET}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching MCP tools: {e.response.status_code} from {openapi_url}")
        print(f"{RED}HTTP error {e.response.status_code} while fetching tools from MCP server.{RESET}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from MCP tools endpoint {openapi_url}: {e}")
        print(f"{RED}Error parsing tool information from MCP server.{RESET}")
    except Exception as e:
        logger.error(f"Unexpected error fetching MCP tools: {e}")
        print(f"{RED}An unexpected error occurred while fetching MCP tools.{RESET}")
    return None

def print_welcome_message(tools: Optional[List[Dict[str, str]]], mcp_api_base: str) -> None:
    """Print welcome message with configuration details."""
    print(f"\n{GREEN}=" * 80)
    print(f"LiteLLM Chat with Ollama and MCP Tools")
    print(f"=" * 80)
    print(f"Model: {OLLAMA_MODEL}")
    print(f"Ollama Server: {OLLAMA_SERVER}")
    print(f"MCP Endpoint: {MCP_ENDPOINT} (Tools fetched from {mcp_api_base})")
    print(f"Log File: {LOG_FILE}")

    print(f"\n{YELLOW}MCP Tools Information:{RESET}")
    if tools:
        print(f"{GREEN}Available MCP Tools:{RESET}")
        for tool in tools:
            print(f"  - {CYAN}{tool['name']}{RESET}: {tool['description']}")
    elif tools is None: # Error occurred during fetch
        print(f"{RED}Could not retrieve tool information from MCP server.{RESET}")
    else: # Empty list, no tools found but no error
        print(f"{YELLOW}No MCP tools seem to be available or registered on the server.{RESET}")
    
    print(f"Type 'exit' or 'quit' to end the chat.")
    print(f"=" * 80 + RESET)

def main() -> None:
    """Run the chat application."""
    setup_litellm()

    mcp_api_base = f"http://{MCP_ENDPOINT}"
    available_tools = fetch_mcp_tools(mcp_api_base)

    print_welcome_message(available_tools, mcp_api_base)

    # Start with a system message to provide context
    system_prompt = "You are a helpful AI assistant with access to various tools through MCP. "
    if available_tools:
        tool_names = [tool['name'] for tool in available_tools]
        if tool_names:
            system_prompt += f"Available tools include: {', '.join(tool_names)}. "
        else:
            system_prompt += "No specific tools appear to be registered. "
    else:
        system_prompt += "Could not determine available tools. "
    
    system_prompt += "Use the appropriate tools when needed to provide accurate and helpful information."

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # Main chat loop
    while True:
        # Get user input
        user_input = input(f"{CYAN}You: {RESET}")

        # Check for exit command
        if user_input.lower() in ["exit", "quit"]:
            print(f"\n{GREEN}Goodbye!{RESET}")
            break

        # Add user message to the conversation
        messages.append({"role": "user", "content": user_input})

        try:
            # Get response from the model (remove tool_choice parameter)
            print(f"\n{YELLOW}Thinking...{RESET}")
            response = completion(
                model=f"ollama/{OLLAMA_MODEL}",
                messages=messages,
                api_base=OLLAMA_SERVER,
                max_tokens=1024,
            )

            # Extract assistant message
            assistant_message = response.choices[0].message

            # Check for tool calls
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                print(f"\n{YELLOW}Using tools to answer your question...{RESET}")

                # Log tool usage
                logger.info(f"Tool calls: {json.dumps(assistant_message.tool_calls, default=str)}")

                # Add the assistant's initial response with tool calls
                messages.append(assistant_message)

                # Get the final response after tool usage
                response = completion(
                    model=f"ollama/{OLLAMA_MODEL}",
                    messages=messages,
                    api_base=OLLAMA_SERVER,
                    max_tokens=1024,
                )

                assistant_message = response.choices[0].message

            # Add the response to the messages
            messages.append({"role": "assistant", "content": assistant_message.content})

            # Display the response
            print(f"\n{GREEN}Assistant: {assistant_message.content}{RESET}\n")

        except Exception as e:
            error_msg = str(e)
            print(f"\n{RED}Error: {error_msg}{RESET}\n")
            logger.error(f"Error in chat completion: {error_msg}")

            # Handle the error gracefully and continue the conversation
            messages.append({
                "role": "assistant",
                "content": f"I encountered an error while processing your request. Please try again or ask something else."
            })

if __name__ == "__main__":
    main()
