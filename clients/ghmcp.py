"""
Interactive Chat Application with GitHub MCP using Python SDK, LiteLLM, and Ollama

This application provides an interactive chat session that interfaces with a local Ollama instance
running the 'granite3.2:8b' model. It uses the 'modelcontextprotocol' Python SDK
to automatically start, manage, and interact with a local GitHub MCP server (Go binary) via stdio.

Features:
- Interactive chat interface
- Uses LiteLLM to communicate with Ollama
- Uses the 'modelcontextprotocol' SDK's stdio_client to manage the server process (Go binary)
- Interacts with the MCP server using ClientSession and call_tool based on documented tools
- Uses asyncio for asynchronous operations
- LLM interprets user requests into MCP commands
- Handles basic MCP actions by calling server tools (search repos, view file, list issues, list PRs)
- Clear prompts and responses
- Error handling for Ollama and MCP SDK interactions
- Uses type annotations and docstrings
- Follows PEP 8 style guidelines

Prerequisites:
- Ollama installed and running locally (https://ollama.ai/)
- 'granite3.2:8b' model pulled in Ollama (ollama pull granite3.2:8b)
- LiteLLM Python package installed (pip install litellm)
- modelcontextprotocol Python SDK installed (pip install modelcontextprotocol)
- GitHub MCP Server (Go binary) downloaded from https://github.com/github/github-mcp-server/releases
    and placed in a known location. Ensure the binary is executable (`chmod +x /path/to/binary`).
- Git installed and configured (likely needed by the MCP server)
- A GitHub Personal Access Token (PAT) configured for the MCP server via the
    GITHUB_PERSONAL_ACCESS_TOKEN environment variable. This variable MUST be accessible
    to the Python script when it runs.

Run the application:
1.    Ensure Ollama is running with the 'granite3.2:8b' model available.
2.    Download the correct 'github-mcp-server' binary for your OS from the releases page.
3.    Make the downloaded binary executable (e.g., `chmod +x ./github-mcp-server`).
4.    ***IMPORTANT***: Update the `MCP_SERVER_BINARY_PATH` variable in this script to the correct path of the downloaded binary.
5.    ***IMPORTANT***: Ensure the GITHUB_PERSONAL_ACCESS_TOKEN environment variable is set *in the environment where you run this Python script*.
        (e.g., `export GITHUB_PERSONAL_ACCESS_TOKEN='your_token_here'` before running python).
6.    Run this Python script. It will attempt to start the MCP server binary via the SDK, passing the token.
7.    Interact with the chat prompts (e.g., "search repositories for 'mcp'",
        "show me the content of README.md in the 'modelcontextprotocol/servers' repo",
        "list issues for 'modelcontextprotocol/servers'").
8.    The SDK will handle stopping the MCP server process on exit.

Important Notes:
- This script now executes a downloaded Go binary, not an npx command.
- You MUST update `MCP_SERVER_BINARY_PATH` below.
- The script now explicitly passes the GITHUB_PERSONAL_ACCESS_TOKEN environment variable
    to the server subprocess. Ensure the variable is set before running this script.
- Tool names and arguments are based on the documentation for the Go-based github-mcp-server.
- Error handling is included, but issues with file permissions, the binary path,
    or GitHub authentication might require manual debugging.
"""

import litellm
import sys
import json
import asyncio
import os  # Import os to check if the binary path exists and read env vars
from typing import List, Dict, Any, Optional

# Import necessary components from the MCP SDK
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Corrected import for McpError based on traceback
from mcp import McpError  # Import base MCP exception directly from 'mcp'

# --- Configuration ---
OLLAMA_MODEL = "llama3.2:3b"

# *** IMPORTANT: UPDATE THIS PATH ***
# Set the full path to the downloaded github-mcp-server executable binary
MCP_SERVER_BINARY_PATH = "/Users/jonesn/bin/github-mcp-server"  # EXAMPLE: "./github-mcp-server" or "/usr/local/bin/github-mcp-server"

# --- Sanity check for binary path ---
if not os.path.exists(MCP_SERVER_BINARY_PATH) or not os.path.isfile(MCP_SERVER_BINARY_PATH):
    print(
        f"Error: The specified MCP server binary path does not exist or is not a file.",
        file=sys.stderr,
    )
    print(f"Path configured: '{MCP_SERVER_BINARY_PATH}'", file=sys.stderr)
    print(
        f"Please download the binary from https://github.com/github/github-mcp-server/releases",
        file=sys.stderr,
    )
    print(f"and update the MCP_SERVER_BINARY_PATH variable in the script.", file=sys.stderr)
    sys.exit(1)

if not os.access(MCP_SERVER_BINARY_PATH, os.X_OK):
    print(f"Error: The specified MCP server binary is not executable.", file=sys.stderr)
    print(f"Path: '{MCP_SERVER_BINARY_PATH}'", file=sys.stderr)
    print(
        f"Please make it executable (e.g., using 'chmod +x {MCP_SERVER_BINARY_PATH}')",
        file=sys.stderr,
    )
    sys.exit(1)


# Configure LiteLLM (remains the same, but call below is adjusted)
litellm.base_url = "http://localhost:11434"
litellm.api_key = "ollama"  # Placeholder for Ollama
# litellm.models configuration might not be strictly needed when provider is specified in call
# litellm.models = [{
#         "model_name": OLLAMA_MODEL,
#         "litellm_provided_model_name": OLLAMA_MODEL, # This might be ignored by acompletion
#         "api_base": "http://localhost:11434"
# }]

# --- MCP SDK Interaction (via call_tool) ---
# Specific SDK functions are removed. We use session.call_tool directly.

# --- LLM Interaction (Async) ---


async def get_llm_response(
    messages: List[Dict[str, str]], model: str = OLLAMA_MODEL
) -> Optional[str]:
    """
    Sends messages to the LLM asynchronously and returns the text response.
    Specifies 'ollama/' prefix for the model name.

    Args:
            messages: List of message dictionaries.
            model: The base name of the language model to use (e.g., "granite3.2:8b").

    Returns:
            The content of the model's response, or None on error.
    """
    try:
        # Prepend 'ollama/' to the model name for LiteLLM completion call
        qualified_model_name = f"ollama/{model}"
        print(f"Attempting LLM call with model: {qualified_model_name}")  # Debug print
        response = await litellm.acompletion(
            model=qualified_model_name,  # Use the qualified name
            messages=messages,
            timeout=60,
            # api_base=litellm.base_url # Explicitly passing base_url might also help sometimes
        )
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content
        else:
            print("\nWarning: LLM response structure unexpected.", file=sys.stderr)
            print(f"Raw response: {response}")  # Debug print raw response
            return None
    except Exception as e:
        # Consider catching specific litellm exceptions if needed
        print(f"\nError sending message to {qualified_model_name}: {e}", file=sys.stderr)
        return None


# --- Main Chat Logic (Async) ---


async def chat_interaction(session: ClientSession) -> None:
    """
    Runs the main interactive chat loop using asyncio and the provided MCP ClientSession.

    Args:
            session: An active MCP ClientSession connected to the server.
    """
    print("\nWelcome to the GitHub MCP Chat (SDK Version)!")
    print("------------------------------------------")
    print(f"Using Ollama model '{OLLAMA_MODEL}'. MCP Server managed via SDK.")
    print("Type 'quit', 'exit', or 'bye' to end the session.")
    print("------------------------------------------")

    # Updated system prompt reflecting actual tool names and required args
    system_prompt = (
        "You are an assistant interacting with a GitHub MCP server via a Python SDK client. "
        "When the user asks to perform an action on a GitHub repository, "
        "formulate a command for the client based on the user's request. "
        "Use the repository owner and name where required. "
        "Available commands formats are:\n"
        "SEARCH_REPOS <query_string>\n"
        "GET_FILE <owner>/<repo> <file_path>\n"  # Adjusted format hint
        "LIST_ISSUES <owner>/<repo>\n"  # Adjusted format hint
        "LIST_PRS <owner>/<repo>\n"  # Adjusted format hint
        # Add other commands based on the tools list as needed (e.g., CREATE_ISSUE)
        "If the user's request matches one of these actions, respond *only* with the command string. "
        "Otherwise, respond naturally as a helpful assistant."
    )
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # List available tools on connection to confirm expectations
    try:
        print("Discovering available MCP tools from the server...")
        tools_response = await session.list_tools()
        # The structure of tools_response depends on the SDK version.
        # Adapt parsing based on actual structure (e.g., tools_response.tools)
        available_tools = []
        if hasattr(tools_response, "tools"):
            available_tools = [tool.name for tool in tools_response.tools]
        elif isinstance(tools_response, list):  # Simple list fallback
            available_tools = [getattr(tool, "name", str(tool)) for tool in tools_response]

        if available_tools:
            print(f"Available tools reported by server: {available_tools}")
        else:
            print("No tools reported by server or unable to parse tool list.")
        # Compare available_tools with the ones we expect from the README.
    except McpError as e:  # Use correct exception name
        print(f"Warning: Could not list tools from MCP server: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: An unexpected error occurred listing tools: {e}", file=sys.stderr)

    while True:
        try:
            loop = asyncio.get_running_loop()
            user_input = await loop.run_in_executor(None, input, "User: ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat...")
            break

        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Exiting chat...")
            break

        messages.append({"role": "user", "content": user_input})
        llm_output = await get_llm_response(messages)

        if llm_output is None:
            print(
                "Assistant: Sorry, I encountered an error trying to process that. Please try again."
            )
            messages.pop()
            continue

        command_parts = llm_output.strip().split()
        command = command_parts[0] if command_parts else ""

        mcp_result: Optional[Any] = None
        executed_command = False
        error_occurred = False

        # --- Command Execution (using session.call_tool with correct tool names/args) ---
        try:
            tool_name: Optional[str] = None
            tool_args: Dict[str, Any] = {}

            # Map LLM-generated commands to actual MCP tool names and arguments
            # These tool names/args are based on the github/github-mcp-server documentation
            if command == "SEARCH_REPOS" and len(command_parts) >= 2:
                tool_name = "search_repositories"
                query = " ".join(command_parts[1:])
                tool_args = {"query": query}
            elif (
                command == "GET_FILE" and len(command_parts) == 3
            ):  # Expecting GET_FILE owner/repo path
                tool_name = "get_file_contents"
                owner_repo_str = command_parts[1]
                path = command_parts[2]
                owner_repo_parts = owner_repo_str.split("/")
                if len(owner_repo_parts) == 2:
                    owner, repo = owner_repo_parts
                    tool_args = {"owner": owner, "repo": repo, "path": path}
                else:
                    print(
                        f"Assistant: Invalid owner/repo format '{owner_repo_str}'. Use owner/repo."
                    )
                    error_occurred = True

            elif (
                command == "LIST_ISSUES" and len(command_parts) == 2
            ):  # Expecting LIST_ISSUES owner/repo
                tool_name = "list_issues"
                owner_repo_str = command_parts[1]
                owner_repo_parts = owner_repo_str.split("/")
                if len(owner_repo_parts) == 2:
                    owner, repo = owner_repo_parts
                    tool_args = {"owner": owner, "repo": repo}
                else:
                    print(
                        f"Assistant: Invalid owner/repo format '{owner_repo_str}'. Use owner/repo."
                    )
                    error_occurred = True

            elif command == "LIST_PRS" and len(command_parts) == 2:  # Expecting LIST_PRS owner/repo
                tool_name = "list_pull_requests"
                owner_repo_str = command_parts[1]
                owner_repo_parts = owner_repo_str.split("/")
                if len(owner_repo_parts) == 2:
                    owner, repo = owner_repo_parts
                    tool_args = {"owner": owner, "repo": repo}
                else:
                    print(
                        f"Assistant: Invalid owner/repo format '{owner_repo_str}'. Use owner/repo."
                    )
                    error_occurred = True

            # Add elif blocks for other tools from the README as needed
            # e.g., create_issue, create_pull_request, etc.

            if tool_name and not error_occurred:
                print(f"Assistant: Okay, calling MCP tool '{tool_name}' with args: {tool_args}...")
                # Call the MCP tool via the session
                mcp_result = await session.call_tool(tool_name, tool_args)
                executed_command = True

        except McpError as e:  # Use correct exception name
            # Handle specific MCP errors (connection, tool not found, execution error)
            print(f"Assistant: Error calling MCP tool '{tool_name}': {e}")
            error_occurred = True
            executed_command = False  # Ensure we don't proceed
        except Exception as e:
            # Catch other errors (e.g., parsing command parts)
            print(f"Assistant: An error occurred while preparing or executing the command: {e}")
            error_occurred = True
            executed_command = False

        # --- Process Results or General Chat ---
        if executed_command:
            # Process and display the result from the MCP tool
            print("MCP SDK Response:")
            try:
                print(json.dumps(mcp_result, indent=2, default=str))
                messages.append({"role": "assistant", "content": llm_output})  # Record command
                messages.append(
                    {
                        "role": "system",
                        "content": f"MCP Tool '{tool_name}' Response: {json.dumps(mcp_result, default=str)}",
                    }
                )
            except TypeError:
                print(str(mcp_result))
                messages.append({"role": "assistant", "content": llm_output})
                messages.append(
                    {
                        "role": "system",
                        "content": f"MCP Tool '{tool_name}' Response: {str(mcp_result)}",
                    }
                )

        elif not error_occurred:  # Only print LLM output if no command was attempted or failed
            # Not a command or command parsing failed, treat as general chat
            print(f"Assistant: {llm_output}")
            messages.append({"role": "assistant", "content": llm_output})
        else:
            # An error occurred during command prep or execution, already printed.
            # Pop the user message that caused the error
            messages.pop()


async def main():
    """Main async function to set up MCP connection and run chat."""
    print("Configuring MCP server parameters...")

    # Prepare environment for the subprocess
    server_env = {}
    GITHUB_PERSONAL_ACCESS_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if GITHUB_PERSONAL_ACCESS_TOKEN:
        # Pass the token to the server environment
        server_env["GITHUB_PERSONAL_ACCESS_TOKEN"] = GITHUB_PERSONAL_ACCESS_TOKEN
        # Optionally inherit other environment variables if needed,
        # but often it's better to pass only what's required.
        # server_env.update(os.environ) # Uncomment to inherit everything
    else:
        # Error if the token is not set in the Python script's environment
        print(
            "Error: GITHUB_PERSONAL_ACCESS_TOKEN environment variable not found.", file=sys.stderr
        )
        print("Please set this environment variable before running the script.", file=sys.stderr)
        print("Example: export GITHUB_PERSONAL_ACCESS_TOKEN='ghp_...'")
        sys.exit(1)

    # Configure StdioServerParameters to run the downloaded binary with the specific environment
    server_params = StdioServerParameters(
        command=MCP_SERVER_BINARY_PATH,  # Execute the binary directly
        args=["stdio"],  # Pass 'stdio' as the argument
        env=server_env,  # Pass the prepared environment
    )

    print(f"Attempting to connect to MCP server via stdio ('{MCP_SERVER_BINARY_PATH} stdio')...")
    try:
        # stdio_client manages the server process lifecycle
        async with stdio_client(server_params) as (read, write):
            print("MCP stdio connection established. Initializing session...")
            async with ClientSession(read, write) as session:
                # Initialize the session (protocol negotiation, capabilities exchange)
                await session.initialize()
                print("MCP session initialized successfully.")

                # Check Ollama connection before starting chat
                print("Checking Ollama connection...")
                # Use the function which now qualifies the model name
                if await get_llm_response([{"role": "user", "content": "Hello"}]) is None:
                    print(
                        f"Error: Cannot reach Ollama server/model {OLLAMA_MODEL}. Please ensure it's running.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                print("Ollama connection successful.")

                # Run the main chat loop with the active session
                await chat_interaction(session)

    except McpError as e:  # Use correct exception name
        print(f"\nFatal MCP Error: Failed to connect or initialize session: {e}", file=sys.stderr)
        print(
            f"Please check the path '{MCP_SERVER_BINARY_PATH}', ensure it's executable, and that the required GITHUB_PERSONAL_ACCESS_TOKEN environment variable is set correctly *before running this script*.",
            file=sys.stderr,
        )
        sys.exit(1)
    except FileNotFoundError:
        # This error now specifically means the binary itself wasn't found at the path
        print(f"Fatal Error: Command '{MCP_SERVER_BINARY_PATH}' not found.", file=sys.stderr)
        print(f"Please ensure the path is correct and the binary exists.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected fatal error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nExiting application.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down.")
        # No explicit cleanup needed here, context managers handle it.
