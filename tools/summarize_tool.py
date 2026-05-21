"""
summarize_tool.py — condenses long text using the same LLM as the agent.
"""

from openai import OpenAI
import config


# Lazy singleton — created on first use so config is fully loaded first.
_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.API_KEY, base_url=config.API_BASE_URL)
    return _client


# ── JSON schema (sent to the LLM) ────────────────────────────────────────────
SCHEMA = {
    "type": "function",
    "function": {
        "name": "summarize",
        "description": (
            "Summarizes a long piece of text. "
            "Use when the user asks for a summary or when you have a lot of text to condense."
        ),
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
}


# ── Implementation ────────────────────────────────────────────────────────────
def summarize(text: str) -> str:
    """Summarizes text using the configured LLM."""
    response = _get_client().chat.completions.create(
        model=config.MODEL,
        messages=[
            {"role": "system", "content": "Summarize the following text concisely."},
            {"role": "user",   "content": text}
        ]
    )
    return response.choices[0].message.content
