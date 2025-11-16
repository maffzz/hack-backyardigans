import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    token = event.get("token")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Tokens")

    res = table.get_item(Key={"token": token})
    if "Item" not in res:
        return {"statusCode": 403, "body": "Token no existe"}

    item = res["Item"]
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if now > item["expires"]:
        return {"statusCode": 403, "body": "Token expirado"}

    return {
        "statusCode": 200,
        "body": {
            "user_id": item["user_id"],
            "role": item["role"],
            "department": item.get("department")
        }
    }
