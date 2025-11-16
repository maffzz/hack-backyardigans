import boto3
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from common.response import response

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)

    user_id = body.get("user_id")
    password = body.get("password")

    if not user_id or not password:
        return response(400, {"error": "user_id y password requeridos"})

    dynamodb = boto3.resource("dynamodb")
    users = dynamodb.Table("Users")

    res = users.get_item(Key={"user_id": user_id})
    if "Item" not in res:
        return response(403, {"error": "Invalid credentials"})

    user = res["Item"]

    if user["password"] != hash_password(password):
        return response(403, {"error": "Invalid credentials"})

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

    return response(200, {
        "token": token,
        "role": user["role"],
        "department": user.get("department")
    })
