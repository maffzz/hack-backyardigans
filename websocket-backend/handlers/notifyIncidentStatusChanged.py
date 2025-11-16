"""
Handler Lambda para notificar cuando cambia el estado de un incidente.
Invocado por el backend.
"""
import json
from common.notifications import notify_incident_status_changed


def handler(event, context):
    """
    Recibe un evento con el incidente actualizado y notifica a todos los conectados.
    """
    try:
        # El evento puede venir de una invocación Lambda directa
        if isinstance(event, dict) and "incident" in event:
            incident = event["incident"]
            old_status = event.get("old_status", "")
            user = event.get("user", {})
        elif isinstance(event, dict) and "body" in event:
            # Si viene de HTTP, parsear el body
            body = json.loads(event.get("body", "{}"))
            incident = body.get("incident", {})
            old_status = body.get("old_status", "")
            user = body.get("user", {})
        else:
            incident = event.get("incident", event)
            old_status = event.get("old_status", "")
            user = event.get("user", {})
        
        notify_incident_status_changed(incident, old_status, user)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Notification sent"})
        }
    except Exception as e:
        print(f"Error en notifyIncidentStatusChanged: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

