import boto3
import uuid
from datetime import datetime
from common.websocket import notify_incident_created
from common.email import notify_incident_by_email
from common.authorize import authorize

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        # Entrada (json)
        body = event.get('body', {})
        if isinstance(body, str):
            import json
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
        
        # Notificar WebSocket (tiempo real)
        notify_incident_created(item)
        
        # Notificar por email (asíncrono según urgencia)
        notify_incident_by_email(item, reporter_id)
        
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