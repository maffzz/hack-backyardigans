import json
import boto3
from datetime import datetime 
import uuid
import traceback
from common.auth import require_role
from common.websocket import notify_comment_added

dynamodb = boto3.resource("dynamodb")
table_evt = dynamodb.Table("IncidenteEventos")

def response(code, body):
    return {
        "statusCode": code,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body)
    }

@require_role(["staff", "authority"])
def handler(event, context):
    try:
        user = event["user"]

        if user["role"] not in ["staff", "admin"]:
            return response(403, {"error": "Permiso denegado"})
        
        incident_id = event["pathParameters"]["id"]
        body = json.loads(event.get("body") or "{}")
        comentario = body.get("comentario")
        
        if not comentario:
            return response(400, {"error": "Falta comentario"})
        
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
        notify_comment_added(incident_id, comentario, user["name"])

        return response(200, {"mensaje": "Comentario agregado"})
    except:
        traceback.print_exc()
        return response(500, {"error": "Error interno"})
