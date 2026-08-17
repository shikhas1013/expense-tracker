from agents import function_tool
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from .db import expenses_table, to_json, USER_ID


@function_tool
def update_expense_category(expense_date: str, new_category: str) -> str:
    """
    Update the category of an existing expense.

    Args:
        expense_date: The expense date (used as sort key) to identify the expense
        new_category: The new category to assign (e.g., "food", "transport", "entertainment")

    Returns:
        JSON string confirming the update or error message
    """
    try:
        expenses_table.update_item(
            Key={"userId": USER_ID, "expenseDate": expense_date},
            UpdateExpression="SET category = :cat",
            ExpressionAttributeValues={":cat": new_category.lower()},
            ConditionExpression="attribute_exists(expenseDate)"
        )
        return to_json({
            "success": True,
            "message": f"Category updated to '{new_category}'"
        })
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return to_json({"error": f"Expense not found with date: {expense_date}"})
        return to_json({"error": str(e)})


@function_tool
def get_categories() -> str:
    """
    Get a list of all unique categories currently used in expenses.

    Returns:
        JSON string containing list of categories and their expense counts
    """
    response = expenses_table.query(
        KeyConditionExpression=Key("userId").eq(USER_ID),
        Limit=200,
        ScanIndexForward=False
    )

    expenses = response.get("Items", [])

    category_counts = {}
    for e in expenses:
        cat = e.get("category", "uncategorized")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return to_json({
        "categories": [
            {"name": cat, "count": count}
            for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])
        ]
    })
