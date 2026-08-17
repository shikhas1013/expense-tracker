from agents import function_tool
from boto3.dynamodb.conditions import Key
from dateutil import parser as date_parser
from .db import expenses_table, to_json, USER_ID
from utils import logger


def parse_date(date_str: str) -> str | None:
    if not date_str:
        return None
    try:
        return date_parser.parse(date_str).strftime("%d %b %Y")
    except Exception:
        return date_str


@function_tool
def get_expenses(
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
    merchant: str | None = None,
    limit: int = 50
) -> str:
    """
    Retrieve the user's expenses from the database.

    Args:
        start_date: Filter expenses on or after this date (e.g., "2024-01-01", "January 1 2024")
        end_date: Filter expenses on or before this date
        category: Filter by expense category (e.g., "food", "transport", "entertainment")
        merchant: Filter by merchant name (partial match supported)
        limit: Maximum number of expenses to return (default 50)

    Returns:
        JSON string containing the list of matching expenses
    """
    logger.info(f"get_expenses called: category={category}, merchant={merchant}, dates={start_date}-{end_date}")

    try:
        response = expenses_table.query(
            KeyConditionExpression=Key("userId").eq(USER_ID),
            Limit=limit,
            ScanIndexForward=False
        )
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return to_json({"error": "Failed to fetch expenses", "expenses": [], "count": 0})

    expenses = response.get("Items", [])

    if category:
        category_lower = category.lower()
        expenses = [e for e in expenses if e.get("category", "").lower() == category_lower]

    if merchant:
        merchant_lower = merchant.lower()
        expenses = [e for e in expenses if merchant_lower in e.get("merchant", "").lower()]

    if start_date:
        start_parsed = parse_date(start_date)
        if start_parsed:
            try:
                start_dt = date_parser.parse(start_parsed)
                expenses = [
                    e for e in expenses
                    if date_parser.parse(e.get("expenseDate", ""), fuzzy=True) >= start_dt
                ]
            except Exception:
                pass

    if end_date:
        end_parsed = parse_date(end_date)
        if end_parsed:
            try:
                end_dt = date_parser.parse(end_parsed)
                expenses = [
                    e for e in expenses
                    if date_parser.parse(e.get("expenseDate", ""), fuzzy=True) <= end_dt
                ]
            except Exception:
                pass

    logger.info(f"get_expenses returning {len(expenses)} results")
    return to_json({"expenses": expenses, "count": len(expenses)})
