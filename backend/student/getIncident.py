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

        path_params = event.get("pathParameters") or {}
        incident_id = path_params.get("id")
        
        if not incident_id:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'ID de incidente requerido'
                }
            }

        result = table.get_item(Key={"incident_id": incident_id})

        if "Item" not in result:
            return {
                'statusCode': 404,
                'body': {
                    'error': 'Incidente no encontrado'
                }
            }

        item = convert_decimals(result["Item"])

        return {
            'statusCode': 200,
            'body': {
                'data': item
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