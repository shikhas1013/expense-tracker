from agents import Agent
from tools.expenses import get_expenses
from tools.summary import get_spending_summary
from tools.budgets import get_budget, set_budget, check_budget_status
from tools.categories import update_expense_category, get_categories
from tools.analysis import analyze_spending_trends, identify_unusual_expenses, suggest_savings


query_agent = Agent(
    name="Query Agent",
    instructions="""
    You are a data retrieval specialist. Your job is to fetch and filter expense data.

    Use get_expenses to retrieve transactions with filters (date, category, merchant).
    Use get_spending_summary to aggregate data by category, merchant, month, or source.
    Use get_categories to list available categories.

    Return factual data without interpretation. The analyst will interpret the results.
    """,
    tools=[get_expenses, get_spending_summary, get_categories]
)


analyst_agent = Agent(
    name="Analyst Agent",
    instructions="""
    You are a financial analyst specializing in personal expense analysis.

    Use analyze_spending_trends to identify patterns over time.
    Use identify_unusual_expenses to flag anomalies.
    Use suggest_savings to provide actionable recommendations.

    Provide clear insights with specific numbers and actionable advice.
    """,
    tools=[analyze_spending_trends, identify_unusual_expenses, suggest_savings, get_spending_summary]
)


budget_agent = Agent(
    name="Budget Agent",
    instructions="""
    You are a budget management specialist.

    Use get_budget to check existing budget limits.
    Use set_budget to create or update budgets.
    Use check_budget_status to compare actual spending vs budgets.

    Help users set realistic budgets and track their progress.
    """,
    tools=[get_budget, set_budget, check_budget_status, get_spending_summary]
)
