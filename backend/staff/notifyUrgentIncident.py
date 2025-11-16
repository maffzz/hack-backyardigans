import json
import boto3
import traceback
import os

SNS = boto3.client("sns")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")


def handler(event, context):
    """
    Lambda para enviar notificaciones de emergencia inmediatas.
    Invocada desde createIncident cuando urgencia = ALTA o tipo = EMERGENCIA
    """
    try:
        # Parsear evento
        if isinstance(event, dict) and "incident" in event:
            incident = event["incident"]
        else:
            incident = event

        if not SNS_TOPIC_ARN:
            print("⚠️ SNS_TOPIC_ARN no configurado")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "SNS no configurado"})
            }

        # Verificar si es urgente
        urgencia = incident.get("urgencia", "").upper()
        tipo = incident.get("tipo", "").upper()
        
        if urgencia != "ALTA" and tipo != "EMERGENCIA":
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No es urgente, no se envía notificación"})
            }

        # Construir mensaje de emergencia
        subject = f"🚨🚨 EMERGENCIA UTEC - {tipo} - {urgencia}"
        
        message = f"""
🚨🚨 ALERTA DE EMERGENCIA - ACCIÓN INMEDIATA REQUERIDA 🚨🚨

TIPO: {tipo}
URGENCIA: {urgencia}
INCIDENT ID: {incident.get('incident_id')}

⚠️ DESCRIPCIÓN:
{incident.get('descripcion', 'N/A')}

📍 UBICACIÓN:
Edificio: {incident.get('ubicacion', {}).get('edificio', 'N/A')}
Piso: {incident.get('ubicacion', {}).get('piso', 'N/A')}

🆔 Reportado por: {incident.get('reporter_id', 'N/A')}
⏰ Hora: {incident.get('created_at', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ REQUIERE ATENCIÓN INMEDIATA ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sistema AlertaUTEC
        """.strip()

        # Enviar notificación
        response = SNS.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message,
            MessageAttributes={
                'urgencia': {
                    'DataType': 'String',
                    'StringValue': 'ALTA'
                },
                'tipo': {
                    'DataType': 'String',
                    'StringValue': tipo
                },
                'incident_id': {
                    'DataType': 'String',
                    'StringValue': incident.get('incident_id', '')
                }
            }
        )

        message_id = response.get('MessageId')
        print(f"✅ Notificación de emergencia enviada. MessageId: {message_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Notificación de emergencia enviada",
                "message_id": message_id
            })
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error enviando notificación",
                "detail": str(e)
            })
        }