import json
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
        dep = event["queryStringParameters"]["departamento"]

        result = table.scan()
        items = result.get("Items", [])

        filtrados = [i for i in items if i.get("departamento") == dep]

        return response(200, {"data": filtrados})

    except:
        traceback.print_exc()
        return response(500, {"error": "Error interno"})
