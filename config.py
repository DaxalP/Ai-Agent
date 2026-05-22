import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────────────────────────────────────
MODEL        = os.getenv("MODEL",        "llama-3.3-70b-versatile")
API_KEY      = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("OPENAI_BASE_URL")

# ── Agent loop ────────────────────────────────────────────────────────────────
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS"))

# ── Paths (resolve relative to this file so the agent works from any cwd) ────
_HERE        = os.path.dirname(os.path.abspath(__file__))
DB_PATH      = os.getenv("DB_PATH",      os.path.join(_HERE, "my_database.db"))
MEMORY_FILE  = os.getenv("MEMORY_FILE",  os.path.join(_HERE, "memory.json"))

# ── Memory ────────────────────────────────────────────────────────────────────
MEMORY_WINDOW = int(os.getenv("MEMORY_WINDOW"))
