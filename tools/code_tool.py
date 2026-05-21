"""
code_tool.py — executes arbitrary Python code in a subprocess sandbox.
"""

import subprocess
import sys


# ── JSON schema (sent to the LLM) ────────────────────────────────────────────
SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_code",
        "description": (
            "Executes Python code and returns the output. "
            "Use for calculations, data processing, or any task that requires running code."
        ),
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
}


# ── Implementation ────────────────────────────────────────────────────────────
def execute_code(code: str) -> str:
    """Runs Python code in an isolated subprocess and returns stdout + stderr."""
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
        return "Error: Code execution timed out after 10 seconds."
    except Exception as e:
        return f"Error: {str(e)}"
