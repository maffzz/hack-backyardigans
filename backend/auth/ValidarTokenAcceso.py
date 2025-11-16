import boto3
import json
from datetime import datetime
from common.response import response

def lambda_handler(event, context):
    # Puede venir como dict directo o dentro de body
    if isinstance(event, dict) and "token" in event:
        token = event.get("token")
    elif isinstance(event, dict) and "body" in event:
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        token = body.get("token")
    else:
        token = event.get("token")

    if not token:
        return response(400, {"error": "Token requerido"})

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Tokens")

    res = table.get_item(Key={"token": token})
    if "Item" not in res:
        return response(403, {"error": "Token no existe"})

    item = res["Item"]
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if now > item["expires"]:
        return response(403, {"error": "Token expirado"})

    return response(200, {
        "user_id": item["user_id"],
        "role": item["role"],
        "department": item.get("department")
    })
