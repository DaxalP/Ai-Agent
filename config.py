"""
config.py — single source of truth for all agent settings.

To override any value, set the corresponding environment variable
(or add it to your .env file). Everything else uses the defaults below.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────────────────────────────────────
MODEL        = os.getenv("MODEL",        "llama-3.3-70b-versatile")
API_KEY      = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("OPENAI_BASE_URL")   # None → uses OpenAI default

# ── Agent loop ────────────────────────────────────────────────────────────────
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 10))

# ── Paths (resolve relative to this file so the agent works from any cwd) ────
_HERE        = os.path.dirname(os.path.abspath(__file__))
DB_PATH      = os.getenv("DB_PATH",      os.path.join(_HERE, "my_database.db"))
MEMORY_FILE  = os.getenv("MEMORY_FILE",  os.path.join(_HERE, "memory.json"))

# ── Memory ────────────────────────────────────────────────────────────────────
# Maximum number of individual messages (user + assistant) kept in memory.
# 20 = 10 Q&A pairs.
MEMORY_WINDOW = int(os.getenv("MEMORY_WINDOW", 20))
