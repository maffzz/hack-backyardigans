import boto3
import traceback
from common.authorize import authorize
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

        reporter_id = user["user_id"]

        result = table.scan()
        mine = [x for x in result.get("Items", []) if x.get("reporter_id") == reporter_id]
        mine = convert_decimals(mine)

        return {
            'statusCode': 200,
            'body': {
                'data': mine
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
