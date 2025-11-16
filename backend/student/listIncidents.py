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
        result = table.scan()
        items = result.get("Items", [])

        return response(200, {"data": items})

    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": str(e)})
