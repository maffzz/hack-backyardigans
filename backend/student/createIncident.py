import boto3
import uuid
import json
from datetime import datetime
from common.websocket import notify_incident_created
from common.authorize import authorize

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")
lambda_client = boto3.client("lambda")

def handler(event, context):
    try:
        # Entrada (json)
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        tipo = body.get('tipo')
        descripcion = body.get('descripcion')
        ubicacion = body.get('ubicacion')
        urgencia = body.get('urgencia')
        
        # Validar campos requeridos
        if not tipo or not descripcion or not ubicacion or not urgencia:
            return {
                'statusCode': 400,
                'body': {'error': 'Faltan campos requeridos'}
            }
        
        # Autorizar usuario
        user = authorize(event)
        if not user:
            return {
                'statusCode': 403,
                'body': {'error': 'Token inválido'}
            }
        
        # Proceso
        reporter_id = user["user_id"]
        
        item = {
            "incident_id": str(uuid.uuid4()),
            "reporter_id": reporter_id,
            "tipo": tipo,
            "descripcion": descripcion,
            "ubicacion": ubicacion,
            "urgencia": urgencia,
            "estado": "pendiente",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=item)
        
        # Notificar WebSocket
        notify_incident_created(item)
        
        # Si es urgente, disparar notificación inmediata por email
        if urgencia.upper() == "ALTA" or tipo.upper() == "EMERGENCIA":
            try:
                lambda_client.invoke(
                    FunctionName="alertautec-backend-dev-notifyUrgentIncident",
                    InvocationType="Event",  # Asíncrono
                    Payload=json.dumps({"incident": item})
                )
                print(f"✅ Notificación urgente disparada para incidente {item['incident_id']}")
            except Exception as e:
                # No fallar si la notificación falla
                print(f"⚠️ Error disparando notificación urgente: {e}")
        
        # Salida (json)
        return {
            'statusCode': 201,
            'body': {
                'message': 'Incidente creado',
                'data': item
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }