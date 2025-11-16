"""
Handler Lambda para notificar cuando se asigna un departamento.
Invocado por el backend.
"""
import json
from common.notifications import notify_department_assigned


def handler(event, context):
    """
    Recibe un evento con la asignación y notifica a todos los conectados.
    """
    try:
        # El evento puede venir de una invocación Lambda directa
        if isinstance(event, dict) and "incident_id" in event:
            incident_id = event["incident_id"]
            department = event.get("department", "")
        elif isinstance(event, dict) and "body" in event:
            # Si viene de HTTP, parsear el body
            body = json.loads(event.get("body", "{}"))
            incident_id = body.get("incident_id", "")
            department = body.get("department", "")
        else:
            incident_id = event.get("incident_id", "")
            department = event.get("department", "")
        
        notify_department_assigned(incident_id, department)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Notification sent"})
        }
    except Exception as e:
        print(f"Error en notifyDepartmentAssigned: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

