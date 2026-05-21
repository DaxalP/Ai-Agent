"""
main.py — CLI entry point for the agent.

Run with:
    python main.py
"""

from agent import run_agent
from memory import load_memory

EXIT_PHRASES = {"exit", "quit", "close", "bye", "q"}


def main() -> None:
    print("Agent is ready. Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Check for exit before sending to the agent
        if user_input.lower().strip("()") in EXIT_PHRASES:
            print("Goodbye!")
            break

        memory = load_memory()
        answer = run_agent(user_input, memory=memory)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
