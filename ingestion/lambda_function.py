import boto3
import decimal
import json
import os
import re
from botocore.exceptions import ClientError

AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
TABLE_NAME = os.environ.get("TABLE_NAME", "ExpenseTracker")
USER_ID = os.environ.get("USER_ID", "default_user")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):

    email_text = event.get("email_text", "")
    email_id = event.get("email_id", "manual")
    user_id = event.get("user_id", USER_ID)

    amount_match = re.search(
        r"Amount:</td>\s*<td[^>]*>SGD(\d+\.\d+)|Amount:\s*SGD(\d+\.\d+)",
        email_text
    )

    merchant_match = re.search(
        r"To:</td>\s*<td[^>]*>(.+?)\s*(?:\(|</td>)|To:\s*(.+)",
        email_text
    )

    transaction_match = re.search(
        r"Date & Time:</td>\s*<td[^>]*>(.+?)</td>|Date & Time:\s*(.+)",
        email_text
    )

    if not amount_match or not merchant_match:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Skipped non-transaction DBS email"
            })
        }

    amount = amount_match.group(1) or amount_match.group(2)
    merchant = (merchant_match.group(1) or merchant_match.group(2)).strip()
    transaction_datetime = (transaction_match.group(1) or transaction_match.group(2)).strip()

    category = event.get("category", "uncategorized")

    if "PAYNOW" in email_text.upper():
        payment = "paynow"
    elif "PAYLAH" in email_text.upper():
        payment = "paylah"
    else:
        payment = "dbs"

    expense = {
        "userId": user_id,
        "emailId": email_id,
        "expenseDate": transaction_datetime,
        "merchant": merchant,
        "amount": decimal.Decimal(amount),
        "category": category,
        "source": payment,
        "rawSnippet": email_text
    }

    try:
        table.put_item(
            Item=expense,
            ConditionExpression="attribute_not_exists(expenseDate)"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Expense Saved!",
                "expense": {
                    **expense,
                    "amount": str(expense["amount"])
                }
            })
        }

    except ClientError as e:

        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Duplicate email skipped"
                })
            }

        raise e
