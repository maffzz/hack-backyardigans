import json
import boto3
from collections import Counter
import traceback

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        result = table.scan()
        items = result.get("Items", [])

        estados = Counter([i.get("estado") for i in items])
        deptos = Counter([i.get("departamento") for i in items if "departamento" in i])

        return {
            'statusCode': 200,
            'body': {
                'por_estado': dict(estados),
                'por_departamento': dict(deptos)
            }
        }

    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': {
                'error': 'Error interno'
            }
        }
