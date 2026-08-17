from collections import defaultdict
from agents import function_tool
from boto3.dynamodb.conditions import Key
from dateutil import parser as date_parser
from .db import expenses_table, to_json, USER_ID


@function_tool
def get_spending_summary(
    group_by: str = "category",
    start_date: str | None = None,
    end_date: str | None = None
) -> str:
    """
    Get aggregated spending summary grouped by a specified field.

    Args:
        group_by: Field to group expenses by. Options: "category", "merchant", "month", "source"
        start_date: Only include expenses on or after this date
        end_date: Only include expenses on or before this date

    Returns:
        JSON string with spending totals grouped by the specified field
    """
    response = expenses_table.query(
        KeyConditionExpression=Key("userId").eq(USER_ID),
        Limit=200,
        ScanIndexForward=False
    )

    expenses = response.get("Items", [])

    if start_date:
        try:
            start_dt = date_parser.parse(start_date)
            expenses = [
                e for e in expenses
                if date_parser.parse(e.get("expenseDate", ""), fuzzy=True) >= start_dt
            ]
        except Exception:
            pass

    if end_date:
        try:
            end_dt = date_parser.parse(end_date)
            expenses = [
                e for e in expenses
                if date_parser.parse(e.get("expenseDate", ""), fuzzy=True) <= end_dt
            ]
        except Exception:
            pass

    summary = defaultdict(lambda: {"total": 0.0, "count": 0})

    for expense in expenses:
        amount = float(expense.get("amount", 0))

        if group_by == "month":
            try:
                dt = date_parser.parse(expense.get("expenseDate", ""), fuzzy=True)
                key = dt.strftime("%Y-%m")
            except Exception:
                key = "unknown"
        elif group_by == "category":
            key = expense.get("category", "uncategorized")
        elif group_by == "merchant":
            key = expense.get("merchant", "unknown")
        elif group_by == "source":
            key = expense.get("source", "unknown")
        else:
            key = expense.get(group_by, "unknown")

        summary[key]["total"] += amount
        summary[key]["count"] += 1

    result = {
        "group_by": group_by,
        "summary": {k: {"total": round(v["total"], 2), "count": v["count"]} for k, v in summary.items()},
        "grand_total": round(sum(v["total"] for v in summary.values()), 2)
    }

    return to_json(result)
