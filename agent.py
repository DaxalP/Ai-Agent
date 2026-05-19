import json
from openai import OpenAI
from tools import execute_code, summarize
from database import query_database
from memory import load_memory, save_memory


client = OpenAI()

# Map tool names → actual Python functions
TOOL_FUNCTIONS = {
    "execute_code": execute_code,
    "summarize": summarize,
    "query_database": query_database,
}

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
        # If no tool calls → LLM is done, save memory and return final answer
        if not message.tool_calls:
            print("[Agent] Done — returning final answer.")
            save_memory(messages)
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

    # If we hit the iteration limit, save memory and return whatever we have
    save_memory(messages)
    return "Agent reached maximum iterations without a final answer."


# ─── MAIN ENTRY POINT ────────────────────────────────────
if __name__ == "__main__":
    print("Agent is ready. Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("quit", "exit"):
            break

        memory = load_memory()
        answer = run_agent(user_input, memory=memory)
        print(f"\nAgent: {answer}\n")
        
        
