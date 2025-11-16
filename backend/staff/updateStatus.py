import json
import boto3
import traceback
from datetime import datetime
from common.auth import get_user_from_request
from common.websocket import notify_incident_status_changed
from common.errors import handle_error, validate_status_change, ValidationError, NotFoundError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")
events_table = dynamodb.Table("IncidenteEventos")

def response(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }

@handle_error
def handler(event, context):
    incident_id = event["pathParameters"]["id"]
    
    try:
        body = json.loads(event.get("body") or "{}")
    except:
        raise ValidationError("Body JSON inválido")
    
    new_status = body.get("estado")
    
    if not new_status:
        raise ValidationError("El campo 'estado' es requerido", "estado")
    
    valid_statuses = ["pendiente", "en_proceso", "resuelto", "cerrado"]
    if new_status not in valid_statuses:
        raise ValidationError(
            f"Estado inválido. Valores válidos: {', '.join(valid_statuses)}",
            "estado"
        )
    
    user = get_user_from_request(event)
    
    # Validar que sea staff o admin
    if user["role"] not in ["staff", "admin"]:
        raise ValidationError("Solo staff o authorities pueden actualizar estados")
    
    # Obtener incidente actual
    try:
        response = table.get_item(Key={"incident_id": incident_id})
        incident = response.get("Item")
        
        if not incident:
            raise NotFoundError("Incidente", incident_id)
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        raise ValidationError("Error al obtener incidente")
    
    # Validar transición de estado
    current_status = incident.get("estado", "pendiente")
    validate_status_change(new_status, current_status)
    
    # Actualizar estado
    table.update_item(
        Key={"incident_id": incident_id},
        UpdateExpression="SET #estado = :estado, updated_at = :updated_at",
        ExpressionAttributeNames={"#estado": "estado"},
        ExpressionAttributeValues={
            ":estado": new_status,
            ":updated_at": datetime.utcnow().isoformat()
        }
    )
    
    # Registrar evento
    event_item = {
        "event_id": f"{incident_id}#{datetime.utcnow().isoformat()}",
        "incident_id": incident_id,
        "tipo_evento": "cambio_estado",
        "detalles": {
            "anterior": current_status,
            "nuevo": new_status,
            "actualizado_por": user["user_id"],
            "nombre_usuario": user["name"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    events_table.put_item(Item=event_item)
    
    # Notificar via WebSocket
    updated_incident = {**incident, "estado": new_status, "updated_at": event_item["timestamp"]}
    notify_incident_status_changed(updated_incident, current_status, user)
    
    return response(200, {
        "message": "Estado actualizado",
        "data": {
            "incident_id": incident_id,
            "estado_anterior": current_status,
            "estado_nuevo": new_status,
            "actualizado_por": user["name"]
        }
    })
