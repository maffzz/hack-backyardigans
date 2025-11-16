import json
import boto3
from collections import Counter
import traceback
from common.response import response

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        result = table.scan()
        items = result.get("Items", [])

        estados = Counter([i.get("estado") for i in items])
        deptos = Counter([i.get("departamento") for i in items if "departamento" in i])

        return response(200, {
            "por_estado": dict(estados),
            "por_departamento": dict(deptos)
        })

    except:
        traceback.print_exc()
        return response(500, {"error": "Error interno"})
