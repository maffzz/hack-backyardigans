import json
import boto3
from datetime import datetime 
import uuid
import traceback
from common.authorize import authorize
from common.websocket import notify_comment_added

dynamodb = boto3.resource("dynamodb")
table_evt = dynamodb.Table("IncidenteEventos")

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
                    'error': 'Permiso denegado'
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
        
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        comentario = body.get("comentario")
        
        if not comentario:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Falta comentario'
                }
            }
        
        event_data = {
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": str(uuid.uuid4()),
            "tipo_evento": "comentario_staff",
            "detalle": {
                "comentario": comentario,
                "agregado_por": user["user_id"]
            }
        }
        
        table_evt.put_item(Item=event_data)

        # Notificar via WebSocket
        notify_comment_added(incident_id, comentario, user.get("user_id", "Usuario"))

        return {
            'statusCode': 200,
            'body': {
                'mensaje': 'Comentario agregado'
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
