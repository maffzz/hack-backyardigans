import json
from common.authorize import authorize
import boto3
from datetime import datetime
import uuid
import traceback
from common.websocket import notify_department_assigned

dynamodb = boto3.resource("dynamodb")
table_inc = dynamodb.Table("Incidentes")
table_evt = dynamodb.Table("IncidenteEventos")

def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        incident_id = path_params.get("id")
        
        if not incident_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'ID de incidente requerido'
                })
            }
        
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        
        # Obtener departamento del body
        departamento = body.get("departamento")
        if not departamento:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Campo departamento requerido'
                })
            }
        
        user = authorize(event)
        if not user:
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Token inválido'
                })
            }
        
        # Solo admin puede asignar departamentos
        if user["role"] != "admin":
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Solo administradores pueden asignar departamentos'
                })
            }
        
        # Actualizar Incidente
        table_inc.update_item(
            Key={"incident_id": incident_id},
            UpdateExpression="SET departamento = :d, updated_at = :u",
            ExpressionAttributeValues={
                ":d": departamento,
                ":u": datetime.utcnow().isoformat()
            }
        )
        
        # Registrar evento
        table_evt.put_item(Item={
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": str(uuid.uuid4()),
            "tipo_evento": "asignacion",
            "detalle": {
                "departamento": departamento,
                "asignado_por": user["user_id"]
            }
        })
        
        # Obtener incidente para notificar
        incident_response = table_inc.get_item(Key={"incident_id": incident_id})
        incident = incident_response.get("Item")
        
        # Notificar via WebSocket
        notify_department_assigned(incident_id, departamento, incident)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Departamento asignado correctamente',
                'departamento': departamento
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