from .expenses import get_expenses
from .summary import get_spending_summary
from .budgets import get_budget, set_budget, check_budget_status
from .categories import update_expense_category, get_categories
from .analysis import analyze_spending_trends, identify_unusual_expenses, suggest_savings

all_tools = [
    get_expenses,
    get_spending_summary,
    get_budget,
    set_budget,
    check_budget_status,
    update_expense_category,
    get_categories,
    analyze_spending_trends,
    identify_unusual_expenses,
    suggest_savings,
]
