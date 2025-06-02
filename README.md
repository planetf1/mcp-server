# MCP Tool Server (`mcp_server.py`)

The `mcp_server.py` script is an asynchronous server designed to expose Python functions as "tools" over various communication transports. It utilizes the `FastMCP` framework to manage tools and handle client interactions. The server comes with built-in tools and supports dynamic loading of custom tools from Python files or directories.

## Features

*   **Multiple Transports**: Supports communication via:
    *   `stdio`: Standard input/output, suitable for direct command-line interaction or integration with other processes.
    *   `sse`: Server-Sent Events, allowing web clients to subscribe to tool outputs (listens on `http://<host>:<port>/sse`).
*   **Built-in Tools**:
    *   `echo`: Returns the parameters it was called with.
    *   `health`: Reports the server's operational status (returns "ready").
*   **Custom Tool Loading**:
    *   Dynamically loads Python functions as tools from specified `.py` files or directories containing `.py` files.
    *   Each tool file must define exactly one function to be exposed as a tool.
    *   Imports within tool files are supported.
*   **Configurable Logging**:
    *   Outputs INFO level messages to the console by default.
    *   Supports detailed DEBUG level logging to a specified file for both the server application and the underlying MCP SDK.
*   **Asynchronous**: Built with `asyncio` for efficient handling of concurrent operations.

## Prerequisites

*   Python 3.x
*   The `mcp` Python package (specifically `mcp.server.fastmcp` is used). Ensure this package is installed in your Python environment.

## Command-Line Usage

### Synopsis

```bash
python mcp_server.py [tools_paths...] [--log FILENAME] [--transport {stdio,sse}] [--port PORT]
```

### Options

*   **`tools_paths`** (positional, zero or more)
    *   Paths to Python tool files or directories containing Python tool files.
    *   If a directory is provided, the server will search for `*.py` files (excluding those starting with `_`).
    *   Example: `./my_tool.py ./utils_directory`
    *   Default: None (only built-in tools will be available if no paths are provided).

*   **`--log FILENAME`**
    *   Enable detailed logging (DEBUG level for the application and MCP SDK) to the specified file.
    *   Includes full details of tool calls, responses, and internal operations.
    *   Console will still show INFO level messages.

*   **`--transport {stdio|sse}`**
    *   Communication transport to use.
    *   `stdio`: Use standard input/output.
    *   `sse`: Use Server-Sent Events. The server will listen on `0.0.0.0` by default.
    *   Default: `stdio`

*   **`--port PORT`**
    *   Port number to use for the SSE transport.
    *   Default: `8080`

## Tool Loading

Custom tools are Python functions that the server can expose.

*   **Definition**: Each Python file (`.py`) intended to be a tool module should define exactly one function. This function will be registered as a tool. The name of the function will be its tool name.
*   **Discovery**:
    *   If a path to a `.py` file is provided, the server attempts to load the tool from that file.
    *   If a path to a directory is provided, the server scans the directory for `.py` files (ignoring files like `__init__.py` or any file starting with an underscore) and attempts to load a tool from each valid file.
*   **Imports**: Tool files can import other modules as needed. The server temporarily adds the tool's directory to `sys.path` during loading to facilitate local imports.

## Examples

### 1. Creating a Custom Tool

Create a Python file, for example, `calculator.py`:

```python
# calculator.py
def add(a: int, b: int) -> int:
    """
    Adds two integers and returns the result.
    """
    print(f"Tool 'add' called with a={a}, b={b}") # Example of internal tool logging
    return a + b
```

### 2. Running the Server

**a) With built-in tools only (stdio transport):**

```bash
python mcp_server.py
```
The server will start, and you can interact with `echo` and `health` tools via its standard input/output (details depend on the `FastMCP` client interaction protocol).

**b) With a custom tool (stdio transport):**

```bash
python mcp_server.py calculator.py
```
Now, the `add` tool from `calculator.py` will also be available.

**c) With a directory of tools and detailed logging (stdio transport):**

Assuming you have a directory named `my_tools` containing `calculator.py` and other tool files:

```bash
mkdir my_tools
mv calculator.py my_tools/
# You can add more .py tool files to my_tools/

python mcp_server.py my_tools --log server.log
```
The server will load all valid tools from the `my_tools` directory. Detailed logs will be written to `server.log`, and INFO messages to the console.

**d) Using SSE transport:**

```bash
python mcp_server.py calculator.py --transport sse --port 8888
```
The server will start and listen for SSE connections on `http://0.0.0.0:8888/sse`. Clients can connect to this endpoint to interact with the `echo`, `health`, and `add` tools.

### Interacting with the Server (Conceptual)

How you interact with the tools depends on the chosen transport and the `FastMCP` client-side implementation.

*   **For `stdio`**: You would typically send JSON-RPC like messages to the server's standard input and receive responses on its standard output.
    ```json
    // Example conceptual input for stdio (actual format depends on FastMCP)
    // {"jsonrpc": "2.0", "method": "add", "params": {"a": 5, "b": 3}, "id": 1}
    ```

*   **For `sse`**: Clients would connect to the `/sse` endpoint. The server would then push messages for tool invocations and responses.

## Logging

*   **Console**: By default, INFO level messages are printed to `stdout`. This includes server startup messages, registered tools, and basic activity.
*   **File Logging (`--log` option)**:
    *   Enables DEBUG level logging for both `mcp_server.py` and the `mcp` SDK.
    *   This is highly verbose and includes:
        *   Detailed tool invocation parameters and results.
        *   Internal server operations.
        *   Debug messages from the MCP SDK.
    *   The log file is written in a format like: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.

## Shutdown

Press `Ctrl+C` to shut down the server gracefully.

```