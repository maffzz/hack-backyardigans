import json
from common import authorize
import boto3
from datetime import datetime
import uuid
import traceback
from common.websocket import notify_department_assigned

dynamodb = boto3.resource("dynamodb")
table_inc = dynamodb.Table("Incidentes")
table_evt = dynamodb.Table("IncidenteEventos")

def response(code, body):
    return {
        "statusCode": code,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": body
    }

def handler(event, context):
    try:
        incident_id = event["pathParameters"]["id"]
        body = event.get("body")


        user = authorize(event)
        if not user:
            return response(403, {"error": "Token inválido"})

        if user["role"] not in ["staff", "admin"]:
            return response(403, {"error": "No autorizado"})

        dep = user.get("department")
        if not dep:
            return response(400, {"error": "Tu usuario no tiene departamento"})


        # update Incidente
        table_inc.update_item(
            Key={"incident_id": incident_id},
            UpdateExpression="SET departamento = :d",
            ExpressionAttributeValues={":d": dep}
        )

        # log event
        table_evt.put_item(Item={
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": str(uuid.uuid4()),
            "tipo_evento": "asignacion",
            "detalle": {"departamento": dep}
        })

        # Obtener incidente para notificar
        incident_response = table_inc.get_item(Key={"incident_id": incident_id})
        incident = incident_response.get("Item")

        # Notificar via WebSocket
        notify_department_assigned(incident_id, dep, incident)

        return response(200, {"mensaje": "Asignado correctamente"})

    except:
        traceback.print_exc()
        return response(500, {"error": "Error interno"})
