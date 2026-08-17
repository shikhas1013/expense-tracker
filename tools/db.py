import boto3
import json
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
TABLE_NAME = os.environ.get("TABLE_NAME", "ExpenseTracker")
BUDGETS_TABLE = os.environ.get("BUDGETS_TABLE", "ExpenseBudgets")
USER_ID = os.environ.get("USER_ID", "default_user")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
expenses_table = dynamodb.Table(TABLE_NAME)
budgets_table = dynamodb.Table(BUDGETS_TABLE)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def to_json(data: dict | list) -> str:
    return json.dumps(data, cls=DecimalEncoder)
