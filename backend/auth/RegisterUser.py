import boto3
import hashlib
import json

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    body = event.get("body")
    
    user_id = body.get("user_id")
    password = body.get("password")
    role = body.get("role")
    department = body.get("department")  # solo staff

    if not user_id or not password or not role:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing fields"})}

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Users")

    table.put_item(Item={
        "user_id": user_id,
        "password": hash_password(password),
        "role": role,
        "department": department if department else None
    })

    return {"statusCode": 200, "body": json.dumps({"message": "User registered"})}
