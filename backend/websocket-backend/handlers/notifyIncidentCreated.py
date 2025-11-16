"""
Handler Lambda para notificar cuando se crea un incidente.
Invocado por el backend.
"""
import json
from common.notifications import notify_incident_created


def handler(event, context):
    """
    Recibe un evento con el incidente creado y notifica a todos los conectados.
    """
    try:
        # El evento puede venir de una invocación Lambda directa
        if isinstance(event, dict) and "incident" in event:
            incident = event["incident"]
        elif isinstance(event, dict) and "body" in event:
            # Si viene de HTTP, parsear el body
            body = event.get("body")
            incident = body.get("incident", body)
        else:
            incident = event
        
        notify_incident_created(incident)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Notification sent"})
        }
    except Exception as e:
        print(f"Error en notifyIncidentCreated: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

