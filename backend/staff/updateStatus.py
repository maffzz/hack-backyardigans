import json
import boto3
import traceback
from datetime import datetime
from common.authorize import authorize
from common.websocket import notify_incident_status_changed
from common.errors import validate_status_change

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")
events_table = dynamodb.Table("IncidenteEventos")

def handler(event, context):
    # ========== CORS HEADERS - CRÍTICO ==========
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'PUT,OPTIONS'
    }
    
    # ========== HANDLE OPTIONS (PREFLIGHT) - DEBE IR PRIMERO ==========
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    try:
        # Autorizar DESPUÉS del OPTIONS
        user = authorize(event)
        if not user:
            return {
                'statusCode': 403,
                'headers': cors_headers,  # ← IMPORTANTE: CORS en todos los responses
                'body': json.dumps({
                    'error': 'Token inválido'
                })
            }
        
        if user["role"] not in ["staff", "admin"]:
            return {
                'statusCode': 403,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Solo staff o admin pueden actualizar estados'
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
        
        body = event.get("body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({
                        'error': 'Body JSON inválido'
                    })
                }
        
        new_status = body.get("estado")
        if not new_status:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': "El campo 'estado' es requerido"
                })
            }
        
        valid_statuses = ["pendiente", "en_proceso", "resuelto", "cerrado"]
        if new_status not in valid_statuses:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': f"Estado inválido. Valores válidos: {', '.join(valid_statuses)}"
                })
            }
        
        # Obtener incidente actual
        result = table.get_item(Key={"incident_id": incident_id})
        incident = result.get("Item")
        
        if not incident:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Incidente no encontrado'
                })
            }
        
        # Validar transición de estado
        current_status = incident.get("estado", "pendiente")
        try:
            validate_status_change(new_status, current_status)
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': str(e)
                })
            }
        
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
                "actualizado_por": user["user_id"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        events_table.put_item(Item=event_item)
        
        # Notificar via WebSocket
        updated_incident = {**incident, "estado": new_status, "updated_at": event_item["timestamp"]}
        notify_incident_status_changed(updated_incident, current_status, user)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,  # ← IMPORTANTE: CORS en success response
            'body': json.dumps({
                'message': 'Estado actualizado',
                'data': {
                    'incident_id': incident_id,
                    'estado_anterior': current_status,
                    'estado_nuevo': new_status,
                    'actualizado_por': user.get("user_id", "Usuario")
                }
            })
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': cors_headers,  # ← IMPORTANTE: CORS en error response
            'body': json.dumps({
                'error': str(e)
            })
        }
