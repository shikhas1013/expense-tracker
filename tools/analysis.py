from agents import function_tool
from boto3.dynamodb.conditions import Key
from collections import defaultdict
from dateutil import parser as date_parser
from datetime import datetime, timedelta
from .db import expenses_table, to_json, USER_ID


@function_tool
def analyze_spending_trends(months: int = 3) -> str:
    """
    Analyze spending trends over recent months to identify patterns.

    Args:
        months: Number of months to analyze (default 3)

    Returns:
        JSON with trend analysis including month-over-month changes and insights
    """
    response = expenses_table.query(
        KeyConditionExpression=Key("userId").eq(USER_ID),
        Limit=500,
        ScanIndexForward=False
    )
    expenses = response.get("Items", [])

    monthly_totals = defaultdict(lambda: {"total": 0.0, "count": 0, "categories": defaultdict(float)})

    for e in expenses:
        try:
            exp_date = date_parser.parse(e.get("expenseDate", ""), fuzzy=True)
            month_key = exp_date.strftime("%Y-%m")
            amount = float(e.get("amount", 0))
            category = e.get("category", "uncategorized")

            monthly_totals[month_key]["total"] += amount
            monthly_totals[month_key]["count"] += 1
            monthly_totals[month_key]["categories"][category] += amount
        except Exception:
            pass

    sorted_months = sorted(monthly_totals.keys(), reverse=True)[:months]

    trends = []
    for i, month in enumerate(sorted_months):
        data = monthly_totals[month]
        trend_entry = {
            "month": month,
            "total": round(data["total"], 2),
            "transaction_count": data["count"],
            "top_categories": sorted(
                [(k, round(v, 2)) for k, v in data["categories"].items()],
                key=lambda x: -x[1]
            )[:5]
        }

        if i < len(sorted_months) - 1:
            prev_month = sorted_months[i + 1]
            prev_total = monthly_totals[prev_month]["total"]
            if prev_total > 0:
                change = ((data["total"] - prev_total) / prev_total) * 100
                trend_entry["change_from_previous"] = f"{change:+.1f}%"

        trends.append(trend_entry)

    return to_json({
        "analysis_period": f"Last {months} months",
        "trends": trends,
        "average_monthly_spend": round(sum(monthly_totals[m]["total"] for m in sorted_months) / len(sorted_months), 2) if sorted_months else 0
    })


@function_tool
def identify_unusual_expenses(threshold_multiplier: float = 2.0) -> str:
    """
    Identify expenses that are unusually high compared to typical spending patterns.

    Args:
        threshold_multiplier: Flag expenses this many times higher than category average (default 2.0)

    Returns:
        JSON with list of unusual expenses and why they were flagged
    """
    response = expenses_table.query(
        KeyConditionExpression=Key("userId").eq(USER_ID),
        Limit=200,
        ScanIndexForward=False
    )
    expenses = response.get("Items", [])

    category_amounts = defaultdict(list)
    for e in expenses:
        category = e.get("category", "uncategorized")
        amount = float(e.get("amount", 0))
        category_amounts[category].append(amount)

    category_stats = {}
    for cat, amounts in category_amounts.items():
        if len(amounts) >= 3:
            avg = sum(amounts) / len(amounts)
            category_stats[cat] = {"average": avg, "count": len(amounts)}

    unusual = []
    for e in expenses[:50]:
        category = e.get("category", "uncategorized")
        amount = float(e.get("amount", 0))

        if category in category_stats:
            avg = category_stats[category]["average"]
            if amount > avg * threshold_multiplier:
                unusual.append({
                    "date": e.get("expenseDate"),
                    "merchant": e.get("merchant"),
                    "amount": amount,
                    "category": category,
                    "category_average": round(avg, 2),
                    "times_higher": round(amount / avg, 1)
                })

    return to_json({
        "threshold": f"{threshold_multiplier}x category average",
        "unusual_expenses": unusual[:10],
        "category_averages": {k: round(v["average"], 2) for k, v in category_stats.items()}
    })


@function_tool
def suggest_savings(target_reduction_percent: float = 10.0) -> str:
    """
    Analyze spending and suggest areas where the user could save money.

    Args:
        target_reduction_percent: Target spending reduction percentage (default 10%)

    Returns:
        JSON with actionable savings suggestions
    """
    response = expenses_table.query(
        KeyConditionExpression=Key("userId").eq(USER_ID),
        Limit=200,
        ScanIndexForward=False
    )
    expenses = response.get("Items", [])

    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    current_month = []
    for e in expenses:
        try:
            exp_date = date_parser.parse(e.get("expenseDate", ""), fuzzy=True)
            if exp_date >= month_start:
                current_month.append(e)
        except Exception:
            pass

    category_spend = defaultdict(lambda: {"total": 0.0, "transactions": []})
    for e in current_month:
        cat = e.get("category", "uncategorized")
        amount = float(e.get("amount", 0))
        category_spend[cat]["total"] += amount
        category_spend[cat]["transactions"].append({
            "merchant": e.get("merchant"),
            "amount": amount
        })

    total_spend = sum(c["total"] for c in category_spend.values())
    target_savings = total_spend * (target_reduction_percent / 100)

    suggestions = []
    sorted_categories = sorted(category_spend.items(), key=lambda x: -x[1]["total"])

    for cat, data in sorted_categories[:5]:
        potential_save = data["total"] * 0.2
        suggestions.append({
            "category": cat,
            "current_spend": round(data["total"], 2),
            "potential_savings": round(potential_save, 2),
            "suggestion": f"Reducing {cat} by 20% would save SGD {potential_save:.2f}",
            "top_merchants": sorted(
                [(t["merchant"], t["amount"]) for t in data["transactions"]],
                key=lambda x: -x[1]
            )[:3]
        })

    return to_json({
        "current_month_total": round(total_spend, 2),
        "target_savings": round(target_savings, 2),
        "suggestions": suggestions
    })
