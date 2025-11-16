import json
from common.auth import require_role
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

@require_role(["staff", "authority"])
def handler(event, context):
    try:
        user = event["user"]

        if user["role"] not in ["staff", "admin"]:
            return response(403, {"error": "No autorizado"})

        dep = user.get("department")
        if not dep:
            return response(400, {"error": "Tu usuario no tiene departamento asignado"})

        result = table.scan()
        items = result.get("Items", [])

        filtrados = [i for i in items if i.get("departamento") == dep]

        return response(200, {"data": filtrados})

    except:
        traceback.print_exc()
        return response(500, {"error": "Error interno"})
