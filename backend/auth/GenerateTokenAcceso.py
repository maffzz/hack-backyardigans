import boto3
import json
import hashlib
import jwt
from datetime import datetime, timedelta
from common.auth import generate_jwt_token

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    body = json.loads(event["body"])

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

    # Generate JWT token instead of UUID
    token = generate_jwt_token({
        "user_id": user_id,
        "role": user["role"],
        "department": user.get("department"),
        "email": user.get("email"),
        "name": user.get("name", "")
    })

    return {
        "statusCode": 200,
        "body": json.dumps({
            "token": token,
            "role": user["role"],
            "department": user.get("department")
        })
    }
