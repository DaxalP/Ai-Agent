# How to Build an AI Agent from Scratch
### A Beginner's Guide — Python + OpenAI GPT-4

---

## What Is an AI Agent?

An AI agent is a program where an LLM (like GPT-4) is given **tools** it can call, and it runs in a **loop** — thinking, taking actions, observing results, and repeating — until it decides it's done.

The three pillars:
- **Brain** → The LLM (GPT-4)
- **Tools** → Functions the LLM can invoke (run code, query DB, summarize...)
- **Loop** → Keep running until the LLM says "I'm finished"

Think of it like a smart assistant who can use a calculator, run a terminal, and look things up — and keeps working until your question is fully answered.

---

## The Agent Loop (The Core Idea)

```
User sends a message
       ↓
  LLM thinks: "What should I do?"
       ↓
  LLM calls a Tool  ←──────────────────┐
       ↓                               │
  Tool runs, returns result            │
       ↓                               │
  LLM sees the result, thinks again    │
       ↓                               │
  Does the LLM want another tool? ─────┘ YES
       ↓ NO
  LLM writes a final answer
       ↓
  Loop ends. Done.
```

**Termination condition**: The loop stops when the LLM returns a regular text message (no tool calls). This is the "I'm done" signal.

---

## Step 1 — Set Up Your Project

```
my_agent/
├── agent.py          # Main agent loop
├── tools.py          # All tool functions
├── memory.py         # Persistent memory (optional)
├── database.py       # DB connection + query helper
└── requirements.txt
```

**Install dependencies:**
```bash
pip install openai sqlite3 requests
```

**requirements.txt:**
```
openai>=1.0.0
```

---

## Step 2 — Define Your Tools

Tools are just Python functions. You describe them to the LLM as JSON schemas so it knows when and how to call them.

### Tool 1: Execute Code
Runs Python code and returns the output.

```python
# tools.py
import subprocess
import sys

def execute_code(code: str) -> str:
    """Runs Python code and returns stdout + stderr."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR: " + result.stderr
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Code timed out after 10 seconds."
    except Exception as e:
        return f"Error: {str(e)}"
```

### Tool 2: Summarize Text
Asks GPT-4 to summarize a piece of text (a nested LLM call).

```python
# tools.py (continued)
from openai import OpenAI
client = OpenAI()  # uses OPENAI_API_KEY env variable

def summarize(text: str) -> str:
    """Summarizes a long piece of text using GPT-4."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Summarize the following text concisely."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content
```

### Tool 3: Query Database
Runs a SQL query against a SQLite database (or any DB you connect).

```python
# database.py
import sqlite3

DB_PATH = "my_database.db"

def query_database(sql: str) -> str:
    """Executes a SQL query and returns the results as a string."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)

        if sql.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()

            if not rows:
                return "No results found."

            # Format as a readable table
            result = " | ".join(columns) + "\n"
            result += "-" * 40 + "\n"
            for row in rows:
                result += " | ".join(str(v) for v in row) + "\n"
            return result
        else:
            conn.commit()
            conn.close()
            return f"Query executed. Rows affected: {cursor.rowcount}"

    except Exception as e:
        return f"Database error: {str(e)}"
```

---

## Step 3 — Tell the LLM About Your Tools

OpenAI's API uses a `tools` parameter. You describe each tool as a JSON schema:

```python
# agent.py

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Executes Python code and returns the output. Use for calculations, data processing, or any task that requires running code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to execute."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize",
            "description": "Summarizes a long piece of text. Use when the user asks for a summary or when you have a lot of text to condense.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to summarize."
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Runs a SQL query against the database. Use for any question about data stored in the DB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to run (e.g. SELECT * FROM users WHERE age > 30)"
                    }
                },
                "required": ["sql"]
            }
        }
    }
]
```

**Key insight**: The description field is critical — the LLM reads it to decide WHEN to use each tool. Write it clearly.

---

## Step 4 — Build the Agent Loop

This is the heart of your agent. It runs until the LLM produces a final answer with no tool calls.

```python
# agent.py
import json
from openai import OpenAI
from tools import execute_code, summarize
from database import query_database

client = OpenAI()

# Map tool names → actual Python functions
TOOL_FUNCTIONS = {
    "execute_code": execute_code,
    "summarize": summarize,
    "query_database": query_database,
}

def run_agent(user_message: str, memory: list = None) -> str:
    """
    Runs the agent loop.
    - user_message: the query from the user
    - memory: optional list of prior messages (persistent memory)
    Returns the final response string.
    """

    # Build the message history
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI assistant with tools. "
                "You can run Python code, summarize text, and query a database. "
                "Use tools when needed. When you have a final answer, just reply directly."
            )
        }
    ]

    # Inject memory from previous sessions (if any)
    if memory:
        messages.extend(memory)

    # Add the new user message
    messages.append({"role": "user", "content": user_message})

    # ─── THE LOOP ───────────────────────────────────────
    MAX_ITERATIONS = 10  # Safety limit to prevent infinite loops
    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"\n[Agent Loop - Iteration {iteration}]")

        # Call the LLM
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"  # Let the LLM decide: use a tool or answer directly
        )

        message = response.choices[0].message

        # Add the LLM's response to the message history
        messages.append(message)

        # ─── TERMINATION CHECK ──────────────────────────
        # If no tool calls → LLM is done, return final answer
        if not message.tool_calls:
            print("[Agent] Done — returning final answer.")
            return message.content

        # ─── TOOL EXECUTION ─────────────────────────────
        # The LLM wants to call one or more tools
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"[Agent] Calling tool: {tool_name} with args: {tool_args}")

            # Run the actual Python function
            if tool_name in TOOL_FUNCTIONS:
                tool_result = TOOL_FUNCTIONS[tool_name](**tool_args)
            else:
                tool_result = f"Error: Unknown tool '{tool_name}'"

            print(f"[Agent] Tool result: {tool_result[:200]}...")  # Preview

            # Feed the result back into the message history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(tool_result)
            })

    # If we hit the iteration limit, return whatever we have
    return "Agent reached maximum iterations without a final answer."


# ─── MAIN ENTRY POINT ────────────────────────────────────
if __name__ == "__main__":
    print("Agent is ready. Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        answer = run_agent(user_input)
        print(f"\nAgent: {answer}\n")
```

---

## Step 5 — Add Memory (Optional but Impressive)

Memory = saving conversation history between sessions so the agent remembers past conversations.

```python
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
```

**Use it in your agent:**
```python
# In agent.py, update the main loop:
from memory import load_memory, save_memory

memory = load_memory()
answer = run_agent(user_input, memory=memory)

# After getting the answer, save the new conversation
save_memory(messages)  # pass the full messages list from run_agent
```

---

## Step 6 — Connect a Real Database

For demo purposes, create a small SQLite database to query:

```python
# setup_demo_db.py  (run this once before the demo)
import sqlite3

conn = sqlite3.connect("my_database.db")
cursor = conn.cursor()

# Create a sample table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        department TEXT,
        salary INTEGER
    )
""")

# Insert sample data
cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?)", [
    (1, "Alice",   "Engineering", 95000),
    (2, "Bob",     "Marketing",   72000),
    (3, "Charlie", "Engineering", 88000),
    (4, "Diana",   "HR",          65000),
    (5, "Eve",     "Engineering", 102000),
])

conn.commit()
conn.close()
print("Database created!")
```

Now your agent can answer questions like:
- *"Who are the engineers in the database?"*
- *"What's the average salary by department?"*
- *"Who earns the most?"*

The LLM will generate the SQL automatically — you just run it.

---

## How It All Fits Together

```
User: "What's the average engineering salary?"
        ↓
Agent Loop — Iteration 1:
  GPT-4 thinks: "I need to query the database"
  → Calls: query_database("SELECT AVG(salary) FROM employees WHERE department='Engineering'")
  → Result: "95000.0"
        ↓
Agent Loop — Iteration 2:
  GPT-4 thinks: "I have the answer now"
  → No tool call → returns: "The average Engineering salary is $95,000."
        ↓
Loop terminates. Final answer returned.
```

---

## The 5 Concepts to Explain in Your Demo

1. **The Loop**: Show the iteration print statements running. The LLM keeps going until it decides it's done.

2. **Tool Calling**: Show GPT-4 picking the right tool based on your descriptions. Ask a math question → it calls `execute_code`. Ask a DB question → it calls `query_database`.

3. **Termination**: Explain that `if not message.tool_calls` is the exit condition. When GPT-4 has enough info, it stops calling tools and just answers.

4. **Message History**: Everything goes into `messages[]`. The LLM sees ALL prior tool results on each iteration — that's how it "knows" what it found.

5. **Memory (bonus)**: Show that it remembers things from the previous session by loading from `memory.json`.

---

## What Terno Does Differently (For Context)

The task says "build something similar to Terno." Terno (terno.db) is a tool that:
- Connects to your real database (Postgres, MySQL, etc.)
- Lets the LLM generate SQL from natural language
- Has schema awareness (it knows your table names and columns)
- Uses SQLShield to block dangerous queries (DROP, DELETE, etc.)

To make your agent closer to Terno, add **schema introspection**:

```python
def get_db_schema() -> str:
    """Returns the database schema as a string, so the LLM knows what tables exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    schema = ""
    for (table,) in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        schema += f"\nTable: {table}\n"
        for col in columns:
            schema += f"  - {col[1]} ({col[2]})\n"
    conn.close()
    return schema
```

Then inject it into your system prompt:
```python
schema = get_db_schema()
system_prompt = f"You are a helpful AI assistant... Here is the database schema:\n{schema}"
```

To add SQLShield-style protection:
```python
BLOCKED_KEYWORDS = ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]

def query_database(sql: str) -> str:
    sql_upper = sql.upper()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in sql_upper:
            return f"Blocked: '{keyword}' operations are not permitted for safety."
    # ... rest of the function
```

---

## Demo Day Checklist

- [ ] Run `setup_demo_db.py` before the demo
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Test with: `"Who earns more than $90,000?"`
- [ ] Test with: `"Calculate 2^32 + 17"`
- [ ] Test with: `"Summarize: [paste a paragraph]"`
- [ ] Show the loop iterations printing in the terminal
- [ ] Explain the termination condition

---

## Full File Structure (Final)

```
my_agent/
├── agent.py          ← Main loop, tool dispatch, run_agent()
├── tools.py          ← execute_code(), summarize()
├── database.py       ← query_database(), get_db_schema()
├── memory.py         ← load_memory(), save_memory()
├── setup_demo_db.py  ← One-time script to populate the DB
└── memory.json       ← Created automatically after first run
```

---

*Good luck on the 22nd! The key insight to communicate: an agent is just a loop where an LLM decides when to use tools and when it's done.*
