import subprocess
import sys
from openai import OpenAI

client = OpenAI()  # uses OPENAI_API_KEY env variable


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