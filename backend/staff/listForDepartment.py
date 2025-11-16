import json
from common.auth import get_user_from_request
import boto3
import traceback

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def response(code, body):
    return {
        "statusCode": code,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body)
    }

def handler(event, context):
    try:
        user = get_user_from_request(event)

        if user["role"] not in ["staff", "admin"]:
            return response(403, {"error": "No autorizado"})

        dep = user["department"]
        result = table.scan()
        items = result.get("Items", [])

        filtrados = [i for i in items if i.get("departamento") == dep]

        return response(200, {"data": filtrados})

    except:
        traceback.print_exc()
        return response(500, {"error": "Error interno"})
