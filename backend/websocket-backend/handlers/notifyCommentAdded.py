"""
Handler Lambda para notificar cuando se agrega un comentario.
Invocado por el backend.
"""
import json
from common.notifications import notify_comment_added


def handler(event, context):
    """
    Recibe un evento con el comentario y notifica a todos los conectados.
    """
    try:
        # El evento puede venir de una invocación Lambda directa
        if isinstance(event, dict) and "incident_id" in event:
            incident_id = event["incident_id"]
            comment = event.get("comment", "")
            commenter_name = event.get("commenter_name", "")
        elif isinstance(event, dict) and "body" in event:
            # Si viene de HTTP, parsear el body
            body = event.get("body")
            incident_id = body.get("incident_id", "")
            comment = body.get("comment", "")
            commenter_name = body.get("commenter_name", "")
        else:
            incident_id = event.get("incident_id", "")
            comment = event.get("comment", "")
            commenter_name = event.get("commenter_name", "")
        
        notify_comment_added(incident_id, comment, commenter_name)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Notification sent"})
        }
    except Exception as e:
        print(f"Error en notifyCommentAdded: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

