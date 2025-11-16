import json
import boto3
import traceback
import os

# Clientes AWS
DYNAMODB = boto3.resource("dynamodb")
INCIDENTS_TABLE = DYNAMODB.Table("Incidentes")
S3 = boto3.client("s3")
SNS = boto3.client("sns")

# Variables de entorno
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

# Mapeo de departamentos a emails (puedes moverlo a DynamoDB después)
DEPARTMENT_EMAILS = {
    "MANTENIMIENTO": "mantenimiento@utec.edu.pe",
    "SEGURIDAD": "seguridad@utec.edu.pe",
    "LIMPIEZA": "limpieza@utec.edu.pe",
    "SECRETARÍA": "secretaria@utec.edu.pe",
    "SOPORTE TECNICO": "soporte@utec.edu.pe",
}


def _parse_event(event):
    """Admite evento directo (dict) o con body JSON."""
    if not event:
        return {}

    body = event.get("body") if isinstance(event, dict) else None
    if body:
        if isinstance(body, str):
            try:
                return json.loads(body)
            except Exception:
                return {}
        if isinstance(body, dict):
            return body

    if isinstance(event, dict):
        return event

    return {}


def _send_email_notification(incident, departamento, s3_bucket, s3_key):
    """
    Envía notificación por email usando SNS.
    """
    if not SNS_TOPIC_ARN:
        print("⚠️ SNS_TOPIC_ARN no configurado, saltando envío de email")
        return False

    try:
        # Construir mensaje
        subject = f"🚨 Nuevo Incidente Asignado - {departamento}"
        
        # Construir URL del reporte en S3
        region = os.environ.get('AWS_REGION', 'us-east-1')
        s3_url = f"https://{s3_bucket}.s3.{region}.amazonaws.com/{s3_key}"
        
        message = f"""
🚨 ALERTA UTEC - Nuevo Incidente Asignado

Departamento: {departamento}
Incident ID: {incident.get('incident_id')}

📋 DETALLES DEL INCIDENTE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tipo: {incident.get('tipo', 'N/A')}
Urgencia: {incident.get('urgencia', 'N/A')}
Estado: {incident.get('estado', 'N/A')}
Descripción: {incident.get('descripcion', 'N/A')}

📍 UBICACIÓN:
{json.dumps(incident.get('ubicacion', {}), indent=2)}

📊 Reporte Completo:
{s3_url}

⏰ Fecha de Creación: {incident.get('created_at', 'N/A')}
🆔 Reportado por: {incident.get('reporter_id', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Por favor, atienda este incidente a la brevedad.

Sistema AlertaUTEC
        """.strip()

        # Publicar en SNS Topic
        response = SNS.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message,
            MessageAttributes={
                'departamento': {
                    'DataType': 'String',
                    'StringValue': departamento
                },
                'urgencia': {
                    'DataType': 'String',
                    'StringValue': incident.get('urgencia', 'MEDIA')
                },
                'incident_id': {
                    'DataType': 'String',
                    'StringValue': incident.get('incident_id', '')
                }
            }
        )

        message_id = response.get('MessageId')
        print(f"✅ Email enviado exitosamente. MessageId: {message_id}")
        return True

    except Exception as e:
        print(f"❌ Error enviando email via SNS: {e}")
        traceback.print_exc()
        return False


def handler(event, context):
    try:
        payload = _parse_event(event)

        incident_id = payload.get("incident_id")
        departamento = payload.get("departamento")
        s3_bucket = payload.get("s3_bucket")
        s3_key = payload.get("s3_key")

        # Validar campos requeridos
        missing = [k for k in ["incident_id", "departamento", "s3_bucket", "s3_key"] 
                   if not payload.get(k)]
        if missing:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Faltan campos requeridos",
                    "missing": missing,
                }),
            }

        # Obtener incidente desde DynamoDB
        resp = INCIDENTS_TABLE.get_item(Key={"incident_id": incident_id})
        incident = resp.get("Item")
        if not incident:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": "Incidente no encontrado",
                    "incident_id": incident_id,
                }),
            }

        # Verificar que el objeto en S3 exista
        try:
            S3.head_object(Bucket=s3_bucket, Key=s3_key)
            s3_exists = True
        except Exception:
            s3_exists = False

        # Enviar notificación por email
        email_sent = _send_email_notification(
            incident, 
            departamento, 
            s3_bucket, 
            s3_key
        )

        # Log para monitoreo
        print(
            f"📧 Notificación a departamento '{departamento}' "
            f"para incidente '{incident_id}'. "
            f"Reporte en s3://{s3_bucket}/{s3_key}, existe={s3_exists}, "
            f"email_enviado={email_sent}"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Notificación procesada correctamente",
                "incident_id": incident_id,
                "departamento": departamento,
                "s3_bucket": s3_bucket,
                "s3_key": s3_key,
                "s3_exists": s3_exists,
                "email_sent": email_sent,
            }),
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error interno al notificar incidente",
                "detail": str(e),
            }),
        }