import boto3
import traceback
import json
from common.helpers import convert_decimals

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        result = table.scan()
        items = result.get("Items", [])
        items = convert_decimals(items)

        return {
            'statusCode': 200,
            'body': {
                'data': items
            }
        }

    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
