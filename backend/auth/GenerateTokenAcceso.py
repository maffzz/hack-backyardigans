import boto3
import json
import hashlib
import uuid
from datetime import datetime, timedelta

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    body = event.get("body")

    user_id = body["user_id"]
    password = body["password"]

    dynamodb = boto3.resource("dynamodb")
    users = dynamodb.Table("Users")

    res = users.get_item(Key={"user_id": user_id})
    if "Item" not in res:
        return {"statusCode": 403, "body": "Invalid credentials"}

    user = res["Item"]

    if user["password"] != hash_password(password):
        return {"statusCode": 403, "body": "Invalid credentials"}

    token = str(uuid.uuid4())
    expires = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

    tokens = dynamodb.Table("Tokens")
    tokens.put_item(Item={
        "token": token,
        "user_id": user_id,
        "role": user["role"],
        "department": user.get("department"),
        "expires": expires
    })

    return {
        "statusCode": 200,
        "body": {
            "token": token,
            "role": user["role"],
            "department": user.get("department")
        }
    }
