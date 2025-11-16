"""
Módulo común para enviar notificaciones via WebSocket.
Usado por los handlers del websocket-backend.
"""
import os
import json
import boto3
from common.db import list_connections, delete_connection

WS_ENDPOINT = os.environ.get("WS_ENDPOINT")

# Inicializar cliente solo si WS_ENDPOINT está configurado
apigw = None
if WS_ENDPOINT:
    try:
        apigw = boto3.client("apigatewaymanagementapi", endpoint_url=WS_ENDPOINT)
    except Exception as e:
        print(f"Error inicializando API Gateway Management API: {e}")


def _post_to_connection(connection_id: str, payload: dict) -> None:
    """
    Envía un mensaje a una conexión WebSocket específica.
    Mismo patrón que handlers/default.py
    """
    if not apigw:
        print("WS_ENDPOINT no configurado, no se puede enviar mensaje WebSocket")
        return
    
    data_bytes = json.dumps(payload).encode("utf-8")
    try:
        apigw.post_to_connection(ConnectionId=connection_id, Data=data_bytes)
    except apigw.exceptions.GoneException:
        # conexión muerta → la eliminamos
        delete_connection(connection_id)
    except Exception as e:
        # en hackatón basta con loguear
        print(f"Error enviando a {connection_id}: {e}")


def broadcast(payload: dict) -> None:
    """
    Envía un mensaje a todas las conexiones activas.
    """
    conns = list_connections()
    for c in conns:
        _post_to_connection(c["connectionId"], payload)


def notify_incident_created(incident: dict) -> None:
    """
    Notifica cuando se crea un nuevo incidente.
    """
    payload = {
        "type": "incident_created",
        "incident": {
            "incident_id": incident.get("incident_id"),
            "tipo": incident.get("tipo"),
            "descripcion": incident.get("descripcion"),
            "ubicacion": incident.get("ubicacion"),
            "urgencia": incident.get("urgencia"),
            "estado": incident.get("estado"),
            "reporter_name": incident.get("reporter_name"),
            "created_at": incident.get("created_at")
        }
    }
    broadcast(payload)


def notify_incident_status_changed(incident: dict, old_status: str, user: dict) -> None:
    """
    Notifica cuando cambia el estado de un incidente.
    """
    payload = {
        "type": "incident_status_changed",
        "incident_id": incident.get("incident_id"),
        "old_status": old_status,
        "new_status": incident.get("estado"),
        "updated_by": user.get("name"),
        "updated_at": incident.get("updated_at")
    }
    broadcast(payload)


def notify_comment_added(incident_id: str, comment: str, commenter_name: str) -> None:
    """
    Notifica cuando se agrega un comentario a un incidente.
    """
    payload = {
        "type": "comment_added",
        "incident_id": incident_id,
        "comment": comment,
        "commenter_name": commenter_name
    }
    broadcast(payload)


def notify_department_assigned(incident_id: str, department: str) -> None:
    """
    Notifica cuando se asigna un departamento a un incidente.
    """
    payload = {
        "type": "department_assigned",
        "incident_id": incident_id,
        "department": department
    }
    broadcast(payload)

