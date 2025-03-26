#!/usr/bin/env python3

# server.py
# see https://github.com/modelcontextprotocol/python-sdk#running-your-server

import importlib
import pkgutil
from mcp_instance import mcp

# Dynamically import all modules from packages
def import_submodules(package_name):
    """Import all modules from a package to register MCP components"""
    package = importlib.import_module(package_name)
    for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
        if not is_pkg:
            importlib.import_module(name)

# Import all components by type
import_submodules('tools')
import_submodules('resources')
import_submodules('prompts')

if __name__ == "__main__":
    mcp.run()
