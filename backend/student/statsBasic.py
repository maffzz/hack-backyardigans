import json
import boto3
import traceback
from collections import Counter
from common.response import response

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        result = table.scan()
        items = result.get("Items", [])

        tipos = [i["tipo"] for i in items if "tipo" in i]
        conteo = Counter(tipos)

        return response(200, {"stats": dict(conteo)})

    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": str(e)})
