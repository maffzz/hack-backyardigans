import json
import boto3
import uuid
import traceback
from decimal import Decimal
from datetime import datetime
from common.websocket import notify_incident_created
from common.authorize import authorize

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")   # TABLA REAL

def decimal_default(obj):
    """Convierte Decimal a float para JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def response(code, body):
    if isinstance(body, dict):
        body_str = json.dumps(body, default=decimal_default)
    elif isinstance(body, str):
        body_str = body
    else:
        body_str = json.dumps({"error": str(body)}, default=decimal_default)
    
    return {
        "statusCode": code,
        "body": body_str
    }

def handler(event, context):
    try:
        print("EVENT:", event)

        body = event.get("body")
        if body is None:
            return response(400, {"error": "Body requerido"})
        
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return response(400, {"error": "Body JSON inválido"})
        
        if not isinstance(body, dict):
            return response(400, {"error": "Body debe ser un objeto JSON"})

        required = ["tipo", "descripcion", "ubicacion", "urgencia"]
        missing = [r for r in required if r not in body]

        if missing:
            return response(400, {"error": f"Faltan campos: {', '.join(missing)}"})

        user = authorize(event)
        if not user:
            return response(403, {"error": "Token inválido"})

        reporter_id = user["user_id"]

        item = {
            "incident_id": str(uuid.uuid4()),
            "reporter_id": reporter_id,
            "tipo": body["tipo"],
            "descripcion": body["descripcion"],
            "ubicacion": body["ubicacion"],
            "urgencia": body["urgencia"],
            "estado": "pendiente",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        table.put_item(Item=item)

        # Enviar notificación WebSocket
        notify_incident_created(item)

        return response(201, {"message": "Incidente creado", "data": item})

    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": str(e)})

