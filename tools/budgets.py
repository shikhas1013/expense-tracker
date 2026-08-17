from decimal import Decimal
from agents import function_tool
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from .db import budgets_table, expenses_table, to_json, USER_ID
from dateutil import parser as date_parser
from datetime import datetime


@function_tool
def get_budget(category: str | None = None) -> str:
    """
    Retrieve budget limits for one or all categories.

    Args:
        category: Specific category to get budget for. If None, returns all budgets.

    Returns:
        JSON string containing budget information
    """
    try:
        if category:
            response = budgets_table.get_item(
                Key={"userId": USER_ID, "category": category.lower()}
            )
            item = response.get("Item")
            if item:
                return to_json({"budget": item})
            return to_json({"budget": None, "message": f"No budget set for {category}"})
        else:
            response = budgets_table.query(
                KeyConditionExpression=Key("userId").eq(USER_ID)
            )
            return to_json({"budgets": response.get("Items", [])})
    except ClientError as e:
        return to_json({"error": str(e)})


@function_tool
def set_budget(category: str, monthly_limit: float) -> str:
    """
    Set or update a monthly budget limit for a category.

    Args:
        category: The expense category (e.g., "food", "transport", "entertainment")
        monthly_limit: The monthly spending limit in SGD

    Returns:
        JSON string confirming the budget was set
    """
    try:
        budgets_table.put_item(
            Item={
                "userId": USER_ID,
                "category": category.lower(),
                "monthlyLimit": Decimal(str(monthly_limit)),
                "updatedAt": datetime.now().isoformat()
            }
        )
        return to_json({
            "success": True,
            "message": f"Budget for {category} set to SGD {monthly_limit:.2f}/month"
        })
    except ClientError as e:
        return to_json({"error": str(e)})


@function_tool
def check_budget_status(category: str | None = None) -> str:
    """
    Check spending against budget for one or all categories for the current month.

    Args:
        category: Specific category to check. If None, checks all categories with budgets.

    Returns:
        JSON string with budget vs actual spending comparison
    """
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    expenses_response = expenses_table.query(
        KeyConditionExpression=Key("userId").eq(USER_ID),
        Limit=200,
        ScanIndexForward=False
    )
    expenses = expenses_response.get("Items", [])

    monthly_expenses = []
    for e in expenses:
        try:
            exp_date = date_parser.parse(e.get("expenseDate", ""), fuzzy=True)
            if exp_date >= month_start:
                monthly_expenses.append(e)
        except Exception:
            pass

    spending_by_category = {}
    for e in monthly_expenses:
        cat = e.get("category", "uncategorized").lower()
        amount = float(e.get("amount", 0))
        spending_by_category[cat] = spending_by_category.get(cat, 0) + amount

    if category:
        budget_response = budgets_table.get_item(
            Key={"userId": USER_ID, "category": category.lower()}
        )
        budget_item = budget_response.get("Item")
        spent = spending_by_category.get(category.lower(), 0)

        if budget_item:
            limit = float(budget_item.get("monthlyLimit", 0))
            return to_json({
                "category": category,
                "budget": limit,
                "spent": round(spent, 2),
                "remaining": round(limit - spent, 2),
                "percentage_used": round((spent / limit) * 100, 1) if limit > 0 else 0,
                "over_budget": spent > limit
            })
        else:
            return to_json({
                "category": category,
                "budget": None,
                "spent": round(spent, 2),
                "message": f"No budget set for {category}"
            })
    else:
        budgets_response = budgets_table.query(
            KeyConditionExpression=Key("userId").eq(USER_ID)
        )
        budgets = {b["category"]: float(b["monthlyLimit"]) for b in budgets_response.get("Items", [])}

        status = []
        for cat, limit in budgets.items():
            spent = spending_by_category.get(cat, 0)
            status.append({
                "category": cat,
                "budget": limit,
                "spent": round(spent, 2),
                "remaining": round(limit - spent, 2),
                "percentage_used": round((spent / limit) * 100, 1) if limit > 0 else 0,
                "over_budget": spent > limit
            })

        return to_json({
            "month": now.strftime("%B %Y"),
            "status": status,
            "total_budgeted": sum(budgets.values()),
            "total_spent": round(sum(spending_by_category.get(c, 0) for c in budgets), 2)
        })
