"""
Módulo para invocar las funciones Lambda del websocket-backend.
El backend invoca estas funciones para enviar notificaciones via WebSocket.
"""
import os
import json
import boto3

# Nombre del servicio websocket-backend (debe coincidir con el serverless.yml)
WEBSOCKET_SERVICE_NAME = os.environ.get("WEBSOCKET_SERVICE_NAME", "websocket-backend")
STAGE = os.environ.get("STAGE", "dev")

# En Lambda, AWS_REGION está disponible automáticamente como variable de entorno del sistema
# No la definimos manualmente porque es reservada
# Si no está disponible (desarrollo local), usar la región por defecto
REGION = os.environ.get("AWS_REGION", "us-east-1")

lambda_client = boto3.client("lambda", region_name=REGION)


def _invoke_function(function_name: str, payload: dict) -> None:
    """
    Invoca una función Lambda del websocket-backend.
    """
    full_function_name = f"{WEBSOCKET_SERVICE_NAME}-{STAGE}-{function_name}"
    
    try:
        response = lambda_client.invoke(
            FunctionName=full_function_name,
            InvocationType="Event",  # Asíncrono, no espera respuesta
            Payload=payload
        )
        print(f"Invocada función {full_function_name}, StatusCode: {response['StatusCode']}")
    except Exception as e:
        # En hackatón basta con loguear, no fallar la operación principal
        print(f"Error invocando {full_function_name}: {e}")


def notify_incident_created(incident: dict) -> None:
    """
    Notifica cuando se crea un nuevo incidente.
    Invoca la función Lambda del websocket-backend.
    """
    _invoke_function("notifyIncidentCreated", {"incident": incident})


def notify_incident_status_changed(incident: dict, old_status: str, user: dict) -> None:
    """
    Notifica cuando cambia el estado de un incidente.
    Invoca la función Lambda del websocket-backend.
    """
    _invoke_function("notifyIncidentStatusChanged", {
        "incident": incident,
        "old_status": old_status,
        "user": user
    })


def notify_comment_added(incident_id: str, comment: str, commenter_name: str) -> None:
    """
    Notifica cuando se agrega un comentario a un incidente.
    Invoca la función Lambda del websocket-backend.
    """
    _invoke_function("notifyCommentAdded", {
        "incident_id": incident_id,
        "comment": comment,
        "commenter_name": commenter_name
    })


def notify_department_assigned(incident_id: str, department: str, incident: dict = None) -> None:
    """
    Notifica cuando se asigna un departamento a un incidente.
    Invoca la función Lambda del websocket-backend.
    """
    _invoke_function("notifyDepartmentAssigned", {
        "incident_id": incident_id,
        "department": department
    })
