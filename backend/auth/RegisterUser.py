import boto3
import hashlib
import json
from common.response import response

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    body = event.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    
    user_id = body.get("user_id")
    password = body.get("password")
    role = body.get("role")
    department = body.get("department")

    if not user_id or not password or not role:
        return response(400, {"error": "Missing fields"})

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Users")

    table.put_item(Item={
        "user_id": user_id,
        "password": hash_password(password),
        "role": role,
        "department": department if department else None
    })

    return response(200, {"message": "User registered"})
