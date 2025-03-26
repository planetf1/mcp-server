#!/usr/bin/env python3
"""
Launcher for the LiteLLM chat application with MCP tools.
This script handles loading environment variables and launching the chat application.
"""

import os
import sys
import subprocess
import asyncio
from dotenv import load_dotenv

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import litellm
        import colorama
        import dotenv
        return True
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        print("Please install required packages with: pip install litellm colorama python-dotenv")
        return False

def check_ollama_running():
    """Check if Ollama server is running."""
    ollama_server = os.environ.get("OLLAMA_SERVER", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "granite3.2:latest")
    
    print(f"Checking if Ollama is running at {ollama_server}...")
    
    try:
        import httpx
        response = httpx.get(f"{ollama_server}/api/tags")
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            if ollama_model in model_names:
                print(f"✅ Ollama is running and model '{ollama_model}' is available.")
                return True
            else:
                print(f"⚠️ Ollama is running but model '{ollama_model}' is not available.")
                print(f"Available models: {', '.join(model_names)}")
                print(f"You may need to pull the model: ollama pull {ollama_model}")
                return False
        else:
            print(f"❌ Ollama server responded with status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to Ollama server: {e}")
        print("Make sure Ollama is installed and running.")
        print("You can install Ollama from: https://ollama.ai/")
        return False

def check_mcp_server_running():
    """Check if MCP server is running."""
    mcp_endpoint = os.environ.get("MCP_ENDPOINT", "localhost:3000")
    
    print(f"Checking if MCP server is running at {mcp_endpoint}...")
    
    try:
        import httpx
        # Change the URL path to just check the host and port, rather than expecting a specific endpoint
        response = httpx.get(f"http://{mcp_endpoint}/", timeout=5.0)
        
        # Consider any response (even 404) as success since it means the server is running
        if 200 <= response.status_code < 500:
            print(f"✅ MCP server is running at {mcp_endpoint}")
            return True
        else:
            print(f"❌ MCP server responded with status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        print("Make sure the MCP server is running.")
        print("You can start the MCP server with: uv run mcp dev server.py")
        return False

def main():
    """Run the chat application."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check if Ollama is running
    if not check_ollama_running():
        print("\nOllama server check failed. Do you want to continue anyway? (y/n)")
        if input().lower() != 'y':
            return 1
    
    # Check if MCP server is running
    if not check_mcp_server_running():
        print("\nMCP server check failed. Do you want to continue anyway? (y/n)")
        if input().lower() != 'y':
            return 1
    
    # Run the chat application
    print("\nStarting LiteLLM chat application...")
    try:
        import litellm_chat_app
        litellm_chat_app.main()
        return 0
    except Exception as e:
        print(f"Error running chat application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
