import boto3
import json
import traceback
from common.authorize import authorize
from common.helpers import convert_decimals

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    # CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    try:
        user = authorize(event)
        if not user:
            return {
                'statusCode': 403,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Token inválido'
                })
            }

        path_params = event.get("pathParameters") or {}
        incident_id = path_params.get("id")
        
        if not incident_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'ID de incidente requerido'
                })
            }

        result = table.get_item(Key={"incident_id": incident_id})

        if "Item" not in result:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Incidente no encontrado'
                })
            }

        item = convert_decimals(result["Item"])

        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'data': item
            })
        }

    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': str(e)
            })
        }