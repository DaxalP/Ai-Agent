"""
memory.py — persists conversation history across sessions.

Saves only genuine user questions and final assistant answers.
Filters out:
  - system and tool-response messages
  - assistant messages that are intermediate tool-calling steps
  - malformed Groq tool-call syntax embedded in assistant content
  - exit/quit commands and their goodbye replies
  - empty messages
"""

import json
import config

EXIT_COMMANDS = {"exit", "exit()", "quit", "quit()", "close", "bye", "q"}
GOODBYE_REPLIES = {"goodbye!", "goodbye", "bye!", "bye"}


def _extract(m) -> tuple[str | None, str, bool]:
    """
    Returns (role, content, has_tool_calls) from either:
      - a plain dict  (user messages, injected tool results), or
      - a ChatCompletionMessage SDK object  (LLM responses).
    Returns (None, "", False) for unrecognised types.
    """
    if isinstance(m, dict):
        return m.get("role"), m.get("content") or "", bool(m.get("tool_calls"))
    if hasattr(m, "role"):
        return m.role, m.content or "", bool(getattr(m, "tool_calls", None))
    return None, "", False


def load_memory() -> list:
    """Load past messages from disk. Returns an empty list if the file doesn't exist."""
    try:
        with open(config.MEMORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_memory(messages: list) -> None:
    """
    Filters the full message history down to storable Q&A pairs
    and writes them to disk (capped at MEMORY_WINDOW messages).
    """
    storable = []

    for m in messages:
        role, content, has_tool_calls = _extract(m)

        # Keep only user and assistant turns
        if role not in ("user", "assistant"):
            continue
        # Skip intermediate assistant steps that are about to call a tool
        if role == "assistant" and has_tool_calls:
            continue
        # Skip injected recovery messages (legacy plain-text format)
        if content.startswith("Tool result for") or content.startswith("[called "):
            continue
        # Skip malformed Groq tool-call syntax — re-injecting it teaches the LLM bad habits
        if role == "assistant" and "<function=" in content:
            continue
        # Skip exit commands and their paired goodbye replies
        if role == "user" and content.lower().strip() in EXIT_COMMANDS:
            continue
        if role == "assistant" and content.strip().lower() in GOODBYE_REPLIES:
            continue
        # Skip empty turns
        if not content.strip():
            continue

        storable.append({"role": role, "content": content})

    recent = storable[-config.MEMORY_WINDOW:]
    with open(config.MEMORY_FILE, "w") as f:
        json.dump(recent, f, indent=2)
