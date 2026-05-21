"""
tools/__init__.py

Auto-registers every tool module and exposes:
  TOOLS          — list of JSON schemas for the LLM
  TOOL_FUNCTIONS — dict mapping tool name → Python callable

To add a new tool:
  1. Create tools/my_tool.py with a SCHEMA dict and an implementation function.
  2. Import the module here and add it to _TOOL_MODULES.
  That's it — TOOLS and TOOL_FUNCTIONS update automatically.
"""

from tools import code_tool, summarize_tool, database_tool

_TOOL_MODULES = [
    code_tool,
    summarize_tool,
    database_tool,
]

# Build the registry from each module's SCHEMA and the function named
# by SCHEMA["function"]["name"].
TOOLS: list[dict] = []
TOOL_FUNCTIONS: dict[str, callable] = {}

for _mod in _TOOL_MODULES:
    _name = _mod.SCHEMA["function"]["name"]
    _fn   = getattr(_mod, _name)          # function must match schema name
    TOOLS.append(_mod.SCHEMA)
    TOOL_FUNCTIONS[_name] = _fn
