"""
agent.py — the core agent loop.

Responsibilities:
  - Build the message history (system prompt + memory + user message)
  - Call the LLM in a loop until it produces a final answer or hits MAX_ITERATIONS
  - Execute tool calls and feed results back into the loop
  - Recover from Groq/Llama malformed tool-call responses
  - Persist memory after every successful response
"""

import json
import re
import time
import uuid

from openai import OpenAI, BadRequestError, RateLimitError

import config
from tools import TOOLS, TOOL_FUNCTIONS
from tools.database_tool import get_db_schema
from memory import load_memory, save_memory


# ── LLM client (lazy singleton) ───────────────────────────────────────────────
_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.API_KEY, base_url=config.API_BASE_URL)
    return _client


# ── Malformed tool-call recovery ──────────────────────────────────────────────
# Groq/Llama sometimes emits tool calls in a non-standard XML-like format
# instead of proper JSON tool_calls. This helper parses and executes them.
_MALFORMED_RE = re.compile(
    r"<function=(\w+)[^{]*(\{.*?\})\s*>?\s*</function>",
    re.DOTALL
)

def _recover_malformed_call(failed_gen: str) -> tuple[str, str] | None:
    """
    Tries to parse a malformed Groq tool call from `failed_gen`.
    Returns (tool_name, json_args_string) on success, or None if unparseable.
    """
    match = _MALFORMED_RE.search(failed_gen)
    if not match:
        return None
    return match.group(1), match.group(2)


# ── Agent loop ────────────────────────────────────────────────────────────────
def run_agent(user_message: str, memory: list | None = None) -> str:
    """
    Runs the ReAct-style agent loop for a single user query.

    Args:
        user_message: The current query from the user.
        memory:       Optional list of prior {role, content} dicts (persistent memory).

    Returns:
        The agent's final plain-text answer.
    """
    db_schema = get_db_schema()

    # Build the message history: system → memory → current user message
    messages: list = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI assistant with access to tools. "
                "You can run Python code, summarize text, and query a SQLite database. "
                "Only use tools when the task genuinely requires them — "
                "do NOT use tools for conversational questions, definitions, or anything "
                "you can answer directly from your own knowledge. "
                "When you have a final answer, reply directly without calling any tool.\n\n"
                "Database schema (SQLite):\n"
                f"{db_schema}"
            )
        }
    ]

    if memory:
        messages.extend(memory)

    messages.append({"role": "user", "content": user_message})

    # ── Loop ─────────────────────────────────────────────────────────────────
    for iteration in range(1, config.MAX_ITERATIONS + 1):
        print(f"\n[Agent Loop - Iteration {iteration}]")

        # ── LLM call ─────────────────────────────────────────────────────────
        try:
            response = _get_client().chat.completions.create(
                model=config.MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto"
            )
            message = response.choices[0].message
            messages.append(message)

        except RateLimitError as e:
            error_body = e.body or {}
            error_msg  = error_body.get("error", {}).get("message", str(e))

            # Daily limit exhausted — no point retrying, tell the user clearly.
            if "tokens per day" in error_msg.lower() or "tpd" in error_msg.lower():
                return (
                    "Daily token limit reached on the Groq API. "
                    "Please wait until tomorrow or upgrade your plan at "
                    "https://console.groq.com/settings/billing"
                )

            # Per-minute / per-request limit — back off and retry.
            wait = config.RATE_LIMIT_RETRY_WAIT
            print(f"[Agent] Rate limit hit — retrying in {wait}s...")
            time.sleep(wait)
            continue  # retry this iteration

        except BadRequestError as e:
            # Groq sometimes generates malformed tool calls — try to recover.
            failed_gen = (e.body or {}).get("failed_generation", "")
            recovered  = _recover_malformed_call(failed_gen)

            if not recovered:
                return f"Agent error: {str(e)}"

            tool_name, raw_args = recovered
            # Groq sometimes escapes single quotes as \' inside the JSON blob,
            # which is invalid JSON (only \" is a legal string escape).
            # Strip them before parsing so json.loads doesn't crash.
            try:
                tool_args = json.loads(raw_args)
            except json.JSONDecodeError:
                tool_args = json.loads(raw_args.replace("\\'", "'"))
            print(f"[Agent] Recovered malformed call → {tool_name}({tool_args})")

            fn     = TOOL_FUNCTIONS.get(tool_name, lambda **_: f"Unknown tool: '{tool_name}'")
            result = fn(**tool_args)
            print(f"[Agent] Tool result: {str(result)[:200]}...")

            # Inject using the proper tool-call message structure so the LLM
            # sees: assistant (decided to call tool) → tool (result).
            # Using fake user/assistant text here confuses the model into
            # thinking it hasn't answered yet, causing duplicate tool calls.
            fake_call_id = f"recovered_{uuid.uuid4().hex[:8]}"
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id":       fake_call_id,
                    "type":     "function",
                    "function": {
                        "name":      tool_name,
                        "arguments": raw_args,
                    }
                }]
            })
            messages.append({
                "role":         "tool",
                "tool_call_id": fake_call_id,
                "content":      str(result),
            })
            continue

        # ── Termination check ─────────────────────────────────────────────────
        if not message.tool_calls:
            print("[Agent] Done — returning final answer.")
            save_memory(messages)
            return message.content

        # ── Tool execution ────────────────────────────────────────────────────
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"[Agent] Calling tool: {tool_name} with args: {tool_args}")

            fn     = TOOL_FUNCTIONS.get(tool_name, lambda **_: f"Unknown tool: '{tool_name}'")
            result = fn(**tool_args)

            print(f"[Agent] Tool result: {str(result)[:200]}...")

            messages.append({
                "role":         "tool",
                "tool_call_id": tool_call.id,
                "content":      str(result)
            })

    return "Agent reached the maximum number of iterations without a final answer."
