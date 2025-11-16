import json
from common.authorize import authorize
import boto3
import traceback
from common.helpers import convert_decimals

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    # Headers CORS para lambda-proxy
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    try:
        # Manejar preflight OPTIONS para CORS
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'OK'})
            }
        
        # Autorizar usuario
        user = authorize(event)
        if not user:
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Token inválido'
                })
            }
        
        # Verificar rol
        if user["role"] not in ["staff", "admin"]:
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({
                    'error': 'No autorizado'
                })
            }
        
        # Parsear el body del request
        body = json.loads(event.get('body', '{}'))
        departamento = body.get('departamento')
        
        # Validar que se envió el departamento
        if not departamento:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Debes proporcionar el campo "departamento" en el body'
                })
            }
        
        # Obtener incidentes y filtrar por departamento
        result = table.scan()
        items = result.get("Items", [])
        filtrados = [i for i in items if i.get("departamento") == departamento]
        filtrados = convert_decimals(filtrados)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'data': filtrados,
                'departamento': departamento,
                'total': len(filtrados)
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'error': 'JSON inválido en el body'
            })
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Error interno',
                'detalle': str(e)
            })
        }