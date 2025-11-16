import json
import boto3
import uuid
import traceback
from datetime import datetime
from common.websocket import notify_incident_created
from common import authorize

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")   # TABLA REAL

def response(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }

def handler(event, context):
    try:
        print("EVENT:", json.dumps(event))

        try:
            body = json.loads(event.get("body") or "{}")
        except:
            return response(400, {"error": "Body JSON inválido"})

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

