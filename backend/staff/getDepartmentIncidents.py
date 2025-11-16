import json
from common.authorize import authorize
import boto3
import traceback
from common.helpers import convert_decimals

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        # Autorizar usuario
        user = authorize(event)
        if not user:
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Token inválido'
                })
            }
        
        # Solo staff y admin pueden listar por departamento
        if user["role"] not in ["staff", "admin"]:
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'No autorizado'
                })
            }
        
        # Obtener departamento desde el JSON body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        departamento = body.get('departamento')
        
        if not departamento:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Debes proporcionar el campo "departamento" en el body'
                })
            }
        
        # Escanear y filtrar por departamento específico
        result = table.scan()
        items = result.get("Items", [])
        filtrados = [i for i in items if i.get("departamento") == departamento]
        filtrados = convert_decimals(filtrados)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'data': filtrados,
                'departamento': departamento,
                'total': len(filtrados)
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'JSON inválido en el body'
            })
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Error interno'
            })
        }

