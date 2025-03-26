# mcp-server
MCP server for experimenting with LLM tools

This has been created to get an understanding of MCP servers, the protocol, and usage within LLMs. It is not intended for reuse!

## Dependencies

* Install 'uv'
* run `uv sync`

## Unit tests

* `uv run pytest`

## Launch the server

`uv run mcp dev server.py`
```
(.venv) ➜  mcp-server git:(main) ✗ uv run mcp dev server.py
Starting MCP inspector...
Proxy server listening on port 3000

🔍 MCP Inspector is up and running at http://localhost:5173 🚀
```

## View the tools

![Image of MCP Inspector](images/mcp_inspector_basic.png)

## Available Tools

| Tool | Description | Backend Service | Required Configuration |
|------|-------------|----------------|------------------------|
| **add** | Simple addition tool | Local computation | None |
| **calculator** | Evaluates mathematical expressions | Local computation | None |
| **calculate_bmi** | Calculates Body Mass Index | Local computation | None |
| **echo** | Returns input text unchanged | Local computation | None |
| **long_task** | Processes files with progress tracking | Local file system | None |
| **duckduckgo_search** | Web search using DuckDuckGo | DuckDuckGo HTML endpoint | None |
| **wikipedia_search** | Searches Wikipedia articles | Wikipedia API | None |
| **fetch_weather** | Gets current weather by location | OpenWeatherMap API | `OPENWEATHER_API_KEY` |
| **openmeteo_forecast** | Gets detailed weather forecasts | Open-Meteo API | None |
| **news_search** | Searches for recent news articles | NewsAPI | `NEWSAPI_KEY` |
| **tavily_search** | AI-powered web search | Tavily API | `TAVILY_API_KEY` |
| **arxiv_search** | Searches academic papers | arXiv API | None |
| **github_get_file** | Retrieves file contents from GitHub | GitHub API | `GITHUB_TOKEN` |
| **github_list_issues** | Lists issues in a repository | GitHub API | `GITHUB_TOKEN` |
| **github_create_issue** | Creates a new issue in a repository | GitHub API | `GITHUB_TOKEN` |
| **github_list_pull_requests** | Lists PRs in a repository | GitHub API | `GITHUB_TOKEN` |
| **github_search_code** | Searches code on GitHub | GitHub API | `GITHUB_TOKEN` |
| **github_user_activity** | Gets a user's GitHub activity summary | GitHub API | `GITHUB_TOKEN` |
| **create_thumbnail** | Creates image thumbnails | Local image processing | None |

### Environment Variable Configuration

To use tools that require API keys, add the following to your environment:

```bash
# Weather services
export OPENWEATHER_API_KEY="your_openweather_api_key"

# News services
export NEWSAPI_KEY="your_newsapi_key"

# Search services
export TAVILY_API_KEY="your_tavily_api_key"

# GitHub tools
export GITHUB_TOKEN="your_github_personal_access_token"
```

### Sample Chat Application

The repository includes a sample chat application that demonstrates how to use MCP tools with the Ollama LLM service.

#### Prerequisites

* Install Ollama from https://ollama.ai/
* Pull the granite model: ollama pull granite3.2:latest (or use any other model)
* Install additional dependencies: uv pip install litellm colorama python-dotenv httpx

#### Configuration

Create a .env file in the project root with your configuration:

```
# Ollama configuration
OLLAMA_SERVER=http://localhost:11434
OLLAMA_MODEL=granite3.2:latest  # Change to any model you have pulled

# MCP server endpoint (default is localhost:3000)
MCP_ENDPOINT=localhost:3000

# Logging configuration
LOG_FILE=chat_interactions.log

# API keys for various services
OPENWEATHER_API_KEY=your_api_key_here
NEWSAPI_KEY=your_api_key_here
TAVILY_API_KEY=your_api_key_here
GITHUB_TOKEN=your_token_here
```

Launch the Chat Application

First, start the MCP server in one terminal:

```
uv run mcp dev server.py
```

Then, run the chat application in another terminal:

```
python run_chat.py
```

Interact with the LLM, which now has access to all the tools provided by the MCP server.

#### Features

* The chat application automatically uses the MCP tools when appropriate
* All interactions are logged to the file specified in LOG_FILE
* Tools will be called when the LLM decides they're needed to answer a question
* Tool parameters are automatically populated based on the LLM's understanding of the query

#### Caveats

* It doesn't yet work with the default model.... work in progress!
