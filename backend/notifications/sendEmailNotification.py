"""
Función Lambda para enviar notificaciones por email usando SNS.
Se ejecuta de forma asíncrona cuando se crea un incidente con urgencia ALTA o MEDIA.
"""
import os
import json
import boto3

sns_client = boto3.client("sns", region_name=os.environ.get("AWS_REGION", "us-east-1"))

# Topic ARN de SNS (se configura en serverless.yml)
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")


def handler(event, context):
    """
    Envía un email usando SNS según la urgencia del incidente.
    """
    try:
        # Obtener datos del evento
        incident = event.get("incident", {})
        reporter_email = event.get("reporter_email", "")
        
        if not incident or not reporter_email:
            print("Error: Faltan datos del incidente o email del reporter")
            return {"statusCode": 400, "body": "Datos incompletos"}
        
        urgencia = incident.get("urgencia", "").upper()
        incident_id = incident.get("incident_id", "N/A")
        tipo = incident.get("tipo", "N/A")
        descripcion = incident.get("descripcion", "N/A")
        ubicacion = incident.get("ubicacion", {})
        
        # Construir mensaje según urgencia
        if urgencia == "ALTA":
            subject = f"🚨 URGENTE: Incidente {incident_id} - {tipo}"
            message = f"""
Se ha creado un incidente URGENTE que requiere atención inmediata.

ID del Incidente: {incident_id}
Tipo: {tipo}
Urgencia: ALTA
Descripción: {descripcion}
Ubicación: {json.dumps(ubicacion, ensure_ascii=False)}
Reportado por: {reporter_email}
Fecha: {incident.get('created_at', 'N/A')}

Por favor, revise este incidente lo antes posible en el sistema.
"""
        elif urgencia == "MEDIA":
            subject = f"⚠️ Incidente {incident_id} - {tipo}"
            message = f"""
Se ha creado un nuevo incidente que requiere atención.

ID del Incidente: {incident_id}
Tipo: {tipo}
Urgencia: MEDIA
Descripción: {descripcion}
Ubicación: {json.dumps(ubicacion, ensure_ascii=False)}
Reportado por: {reporter_email}
Fecha: {incident.get('created_at', 'N/A')}

Por favor, revise este incidente cuando sea posible.
"""
        else:
            # No enviar email para urgencia BAJA
            print(f"Urgencia {urgencia} no requiere notificación por email")
            return {"statusCode": 200, "body": "No se envía email para esta urgencia"}
        
        # Enviar email usando SNS
        if not SNS_TOPIC_ARN:
            print("Error: SNS_TOPIC_ARN no configurado")
            return {"statusCode": 500, "body": "SNS no configurado"}
        
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        
        print(f"Email enviado exitosamente. MessageId: {response['MessageId']}")
        
        return {
            "statusCode": 200,
            "body": {
                "message": "Email enviado exitosamente",
                "messageId": response["MessageId"]
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error enviando email: {str(e)}")
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }

