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

def save_memory(messages: list):
    """Save recent messages to disk. Keep only the last 20 to avoid bloat."""
    # Filter out system messages and tool calls (keep user + assistant only)
    storable = [
        m for m in messages
        if isinstance(m, dict) and m.get("role") in ("user", "assistant")
        and m.get("content")
    ]
    # Keep last 20 exchanges
    recent = storable[-20:]
    with open(MEMORY_FILE, "w") as f:
        json.dump(recent, f, indent=2)