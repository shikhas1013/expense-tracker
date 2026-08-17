import logging
# Suppress noisy HTTP logs from OpenAI SDK
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

from orchestration import coordinator_agent, run_with_reflection
from orchestration.coordinator import session
from agents import Runner
from utils import logger

leave = ["exit", "quit"]

print("Expense Tracker Multi-Agent System")
print("Type 'exit' or 'quit' to leave")
print("-" * 40)

use_reflection = input("Enable reflection loop? (y/n): ").lower().startswith("y")
print()

while True:
    try:
        question = input("You: ")
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        break

    if question.lower() in leave:
        print("Goodbye!")
        break

    if not question.strip():
        continue

    try:
        if use_reflection:
            response = run_with_reflection(question)
        else:
            result = Runner.run_sync(
                coordinator_agent,
                question,
                session=session
            )
            response = result.final_output
    except KeyboardInterrupt:
        print("\n[Interrupted]")
        continue
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        response = f"Sorry, something went wrong. Please try again. (Error: {type(e).__name__})"

    print(f"\nAgent: {response}\n")