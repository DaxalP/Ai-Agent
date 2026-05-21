# memory.py
import json
import os

MEMORY_FILE = "memory.json"

def load_memory() -> list:
    """Load past messages from disk."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def _extract(m) -> tuple:
    """Extract (role, content, has_tool_calls) from either a dict or a
    ChatCompletionMessage object. Returns (None, None, False) for unknown types."""
    if isinstance(m, dict):
        role = m.get("role")
        content = m.get("content") or ""
        has_tool_calls = bool(m.get("tool_calls"))
        return role, content, has_tool_calls
    # OpenAI / Groq SDK object (ChatCompletionMessage)
    if hasattr(m, "role"):
        role = m.role
        content = m.content or ""
        has_tool_calls = bool(getattr(m, "tool_calls", None))
        return role, content, has_tool_calls
    return None, None, False

def save_memory(messages: list):
    """Save only genuine user questions and final assistant answers.
    Filters out:
    - system messages
    - tool response messages
    - assistant messages that contain tool_calls (intermediate steps)
    - injected tool result lines and [called ...] markers
    Handles both plain dicts and ChatCompletionMessage SDK objects.
    """
    storable = []
    for m in messages:
        role, content, has_tool_calls = _extract(m)

        # Skip system messages, tool response messages, unknown types
        if role not in ("user", "assistant"):
            continue
        # Skip assistant messages that are intermediate tool-calling steps
        if role == "assistant" and has_tool_calls:
            continue
        # Skip injected tool result messages (malformed tool call recovery)
        if content.startswith("Tool result for"):
            continue
        # Skip placeholder assistant messages from malformed tool call recovery
        if content.startswith("[called "):
            continue
        # Skip empty content
        if not content.strip():
            continue
        # Skip assistant messages that contain malformed Groq tool-call syntax
        # — storing these re-teaches the LLM the broken format on the next turn
        if role == "assistant" and "<function=" in content:
            continue

        storable.append({"role": role, "content": content})

    # Keep only the last 10 genuine Q&A pairs (20 messages)
    recent = storable[-20:]
    with open(MEMORY_FILE, "w") as f:
        json.dump(recent, f, indent=2)