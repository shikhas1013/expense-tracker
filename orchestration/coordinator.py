from agents import Agent, Runner, SQLiteSession, handoff
from dotenv import load_dotenv
from .specialists import query_agent, analyst_agent, budget_agent
from utils import logger, retry, fallback

load_dotenv()

session = SQLiteSession("expense-tracker-multi-agent")

# ANSI color codes for terminal output
class Colors:
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


coordinator_agent = Agent(
    name="Expense Coordinator",
    instructions="""
    You are the coordinator for an expense tracking system. Route user requests to specialists:

    1. **Query Agent**: For retrieving expenses, filtering transactions, listing categories
       - "Show my expenses", "What did I spend at...", "List transactions from..."

    2. **Analyst Agent**: For insights, trends, anomalies, and savings advice
       - "Analyze my spending", "Any unusual expenses?", "How can I save money?"

    3. **Budget Agent**: For budget creation, updates, and tracking
       - "Set a budget", "Am I over budget?", "What's my budget for..."

    After receiving results from a specialist, synthesize the information and provide
    a clear, helpful response to the user. If the response seems incomplete or unclear,
    ask the specialist for clarification.
    """,
    handoffs=[
        handoff(query_agent, tool_name_override="route_to_query_agent"),
        handoff(analyst_agent, tool_name_override="route_to_analyst_agent"),
        handoff(budget_agent, tool_name_override="route_to_budget_agent"),
    ]
)


@retry(max_attempts=3, delay=1.0)
def _run_agent(agent, input_text: str, use_session: bool = True):
    """Run an agent with retry logic."""
    if use_session:
        return Runner.run_sync(agent, input_text, session=session)
    return Runner.run_sync(agent, input_text)


def run_with_reflection(user_input: str, max_iterations: int = 2, verbose: bool = True) -> str:
    """
    Run the coordinator with a reflection loop to verify response quality.

    Args:
        user_input: The user's question or request
        max_iterations: Maximum refinement iterations (default 2)
        verbose: Print reflection logs (default True)

    Returns:
        Final response after reflection
    """
    def log(stage: str, message: str, color: str = Colors.CYAN):
        if verbose:
            print(f"{color}{Colors.BOLD}[{stage}]{Colors.RESET} {message}")

    reflection_agent = Agent(
        name="Reflection Agent",
        instructions="""
        You are a quality checker for expense tracking responses.

        Review the response and check:
        1. Does it directly answer the user's question?
        2. Are specific numbers provided where relevant?
        3. Is the advice actionable?
        4. Is anything missing or unclear?

        If the response is good, output: APPROVED: <reason>
        If it needs improvement, output: IMPROVE: <what's missing or wrong>
        """
    )

    logger.info(f"Processing request: {user_input[:50]}...")
    log("Coordinator", "Generating initial response...", Colors.CYAN)

    try:
        result = _run_agent(coordinator_agent, user_input)
        current_response = result.final_output
    except Exception as e:
        logger.error(f"Coordinator failed: {e}")
        return f"Sorry, I encountered an error processing your request. Please try again. (Error: {type(e).__name__})"

    log("Initial Response", current_response[:200] + "..." if len(current_response) > 200 else current_response, Colors.YELLOW)

    for i in range(max_iterations):
        log("Reflection", f"Iteration {i + 1}/{max_iterations} - Evaluating response quality...", Colors.CYAN)

        reflection_input = f"""
        User asked: {user_input}

        Response given: {current_response}

        Evaluate this response.
        """

        try:
            reflection_result = _run_agent(reflection_agent, reflection_input, use_session=False)
            reflection_output = reflection_result.final_output
        except Exception as e:
            logger.warning(f"Reflection failed, skipping: {e}")
            break

        if reflection_output.startswith("APPROVED"):
            reason = reflection_output.replace("APPROVED:", "").strip()
            log("Reflection", f"APPROVED - {reason[:100]}", Colors.GREEN)
            break

        if reflection_output.startswith("IMPROVE"):
            improvement_needed = reflection_output.replace("IMPROVE:", "").strip()
            log("Reflection", f"NEEDS IMPROVEMENT - {improvement_needed[:100]}", Colors.RED)

            log("Coordinator", "Refining response based on feedback...", Colors.CYAN)

            followup = f"""
            The user originally asked: {user_input}

            Your previous response: {current_response}

            This needs improvement: {improvement_needed}

            Please provide an improved response.
            """

            try:
                improved_result = _run_agent(coordinator_agent, followup)
                current_response = improved_result.final_output
                log("Refined Response", current_response[:200] + "..." if len(current_response) > 200 else current_response, Colors.YELLOW)
            except Exception as e:
                logger.warning(f"Refinement failed, using previous response: {e}")
                break
    else:
        log("Reflection", f"Max iterations ({max_iterations}) reached", Colors.YELLOW)

    logger.info("Request completed successfully")
    log("Complete", "Final response ready", Colors.GREEN)
    return current_response
