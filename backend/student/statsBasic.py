import boto3
import traceback
from collections import Counter

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        result = table.scan()
        items = result.get("Items", [])

        tipos = [i["tipo"] for i in items if "tipo" in i]
        conteo = Counter(tipos)

        return {
            'statusCode': 200,
            'body': {
                'stats': dict(conteo)
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
