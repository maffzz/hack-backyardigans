import json
import boto3
import traceback
from common.response import response

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        result = table.scan()
        items = result.get("Items", [])

        return response(200, {"data": items})

    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": str(e)})
