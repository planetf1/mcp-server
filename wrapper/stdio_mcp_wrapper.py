#!/usr/bin/env python3
"""
Lightweight MCP Server to wrap a stdio-based executable as an MCP tool.

This script takes an executable and its arguments, and exposes it as a single
MCP tool over HTTP using FastMCP. The wrapped executable is expected to
read a JSON string from its stdin and print a JSON string to its stdout.
"""

import argparse
import subprocess
import json
import sys
import os
import shlex
from typing import Dict, List, Any, Union

from mcp.server.fastmcp import FastMCP

# Create an MCP server instance globally so the decorator can find it
mcp = FastMCP("StdioWrapperMCPServer")

async def run_external_command(
    executable: str,
    exec_args: List[str],
    input_data: Dict[str, Any],
    custom_env_vars: List[str], # List of "KEY=VALUE" strings
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Runs the external command with the given input data.
    """
    command = [executable] + exec_args
    input_json_str = json.dumps(input_data)

    # Prepare environment for the subprocess
    # Start with a copy of the current environment
    env_for_subprocess = os.environ.copy()
    # Apply custom environment variables
    for env_var_setting in custom_env_vars:
        if "=" in env_var_setting:
            key, value = env_var_setting.split("=", 1)
            env_for_subprocess[key] = value
            print(f"Setting env for subprocess: {key}={value}", file=sys.stderr)

    try:
        print(f"Executing command: {' '.join(shlex.quote(c) for c in command)}", file=sys.stderr)
        print(f"Stdin to command: {input_json_str}", file=sys.stderr)

        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env_for_subprocess
        )
        stdout_data, stderr_data = process.communicate(input=input_json_str, timeout=timeout)

        print(f"Stdout from command: {stdout_data}", file=sys.stderr)
        if stderr_data:
            print(f"Stderr from command: {stderr_data}", file=sys.stderr)

        if process.returncode != 0:
            error_message = f"Command '{' '.join(command)}' failed with exit code {process.returncode}."
            if stderr_data:
                error_message += f"\nStderr: {stderr_data}"
            raise Exception(error_message)

        try:
            output_data = json.loads(stdout_data)
            return output_data
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to decode JSON from command stdout: {e}\nStdout: {stdout_data}")

    except FileNotFoundError:
        raise Exception(f"Executable '{executable}' not found.")
    except subprocess.TimeoutExpired:
        raise Exception(f"Command '{' '.join(command)}' timed out after {timeout} seconds.")
    except Exception as e:
        # Re-raise other exceptions, possibly with more context
        raise Exception(f"Error executing command '{' '.join(command)}': {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Wrap a stdio executable as an MCP tool.")
    parser.add_argument("--executable", required=True, help="Path to the executable to wrap.")
    parser.add_argument("--args", nargs='*', default=[], help="Arguments for the executable.")
    parser.add_argument("--tool-name", default="stdio_tool", help="Name of the MCP tool.")
    parser.add_argument("--tool-description", default="Executes a wrapped stdio command.", help="Description of the MCP tool.")
    parser.add_argument("--port", type=int, default=3001, help="Port for the MCP server to listen on.")
    parser.add_argument("--host", default="0.0.0.0", help="Host for the MCP server to bind to.")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds for the external command.")
    parser.add_argument("--env", action='append', default=[], help="Environment variables to set for the command (e.g., VAR=value). Can be used multiple times.")

    cli_args = parser.parse_args()

    # Define the tool function dynamically using the parsed arguments
    # The mcp.tool decorator needs to be applied at definition time.
    # We use a closure to capture cli_args for the tool function.

    # This is a bit of a workaround as @mcp.tool needs to decorate a function directly.
    # We'll define the tool function inside main after parsing args.

    @mcp.tool(
        name=cli_args.tool_name,
        description=cli_args.tool_description,
        # FastMCP infers schema from type hints.
        # Input: a JSON object, Output: a JSON object
    )
    async def dynamic_stdio_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP tool function that executes the configured external command.
        The 'payload' argument will be passed as JSON to the command's stdin.
        The command's stdout (JSON) will be returned.
        """
        return await run_external_command(
            cli_args.executable,
            cli_args.args,
            payload,
            cli_args.env,
            cli_args.timeout
        )

    print(f"Starting MCP server for tool '{cli_args.tool_name}' on {cli_args.host}:{cli_args.port}")
    print(f"Wrapping executable: {cli_args.executable} {' '.join(cli_args.args)}")
    mcp.run(host=cli_args.host, port=cli_args.port)

if __name__ == "__main__":
    main()