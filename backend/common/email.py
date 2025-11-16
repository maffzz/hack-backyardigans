"""
Módulo para enviar notificaciones por email usando SNS.
Se invoca de forma asíncrona cuando se crea un incidente según su urgencia.
"""
import os
import json
import boto3

# Nombre del servicio (debe coincidir con el serverless.yml)
SERVICE_NAME = os.environ.get("SERVICE_NAME", "alertautec-backend")
STAGE = os.environ.get("STAGE", "dev")
REGION = os.environ.get("AWS_REGION", "us-east-1")

lambda_client = boto3.client("lambda", region_name=REGION)


def _invoke_email_notification(payload: dict) -> None:
    """
    Invoca la función Lambda de notificación por email de forma asíncrona.
    """
    function_name = f"{SERVICE_NAME}-{STAGE}-sendEmailNotification"
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="Event",  # Asíncrono
            Payload=json.dumps(payload)
        )
        print(f"Notificación por email invocada: {function_name}, StatusCode: {response['StatusCode']}")
    except Exception as e:
        # No fallar la operación principal si falla el email
        print(f"Error invocando notificación por email: {e}")


def notify_incident_by_email(incident: dict, reporter_email: str) -> None:
    """
    Notifica por email cuando se crea un incidente según su urgencia.
    Solo envía email para urgencias ALTA y MEDIA.
    """
    urgencia = incident.get("urgencia", "").upper()
    
    # Solo enviar email para urgencias ALTA y MEDIA
    if urgencia in ["ALTA", "MEDIA"]:
        _invoke_email_notification({
            "incident": incident,
            "reporter_email": reporter_email
        })

