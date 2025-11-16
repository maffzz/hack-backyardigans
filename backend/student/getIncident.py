import json
import boto3
import traceback

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def response(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }

def handler(event, context):
    try:
        user = authorize(event)
        if not user:
            return response(403, {"error": "Token inválido"})

        incident_id = event["pathParameters"]["id"]

        result = table.get_item(Key={"incident_id": incident_id})

        if "Item" not in result:
            return response(404, {"error": "Incidente no encontrado"})

        return response(200, {"data": result["Item"]})

    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": str(e)})
