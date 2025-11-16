import boto3
import traceback
from common.response import response
from common.authorize import authorize

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        user = authorize(event)
        if not user:
            return response(403, {"error": "Token inválido"})

        reporter_id = user["user_id"]

        result = table.scan()
        mine = [x for x in result.get("Items", []) if x.get("reporter_id") == reporter_id]

        return response(200, {"data": mine})

    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": str(e)})
