import json
from common.authorize import authorize
import boto3
import traceback
from common.helpers import convert_decimals

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        user = authorize(event)
        if not user:
            return {
                'statusCode': 403,
                'body': {
                    'error': 'Token inválido'
                }
            }

        if user["role"] not in ["staff", "admin"]:
            return {
                'statusCode': 403,
                'body': {
                    'error': 'No autorizado'
                }
            }

        dep = user.get("department")
        if not dep:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Tu usuario no tiene departamento asignado'
                }
            }

        result = table.scan()
        items = result.get("Items", [])

        filtrados = [i for i in items if i.get("departamento") == dep]
        filtrados = convert_decimals(filtrados)

        return {
            'statusCode': 200,
            'body': {
                'data': filtrados
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
