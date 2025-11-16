"""
Script de prueba para verificar que las notificaciones por email funcionen.
Ejecuta este script después de crear un incidente para verificar los logs.
"""
import boto3
import json
import os

# Configuración
REGION = os.environ.get("AWS_REGION", "us-east-1")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "alertautec-backend")
STAGE = os.environ.get("STAGE", "dev")

lambda_client = boto3.client("lambda", region_name=REGION)
sns_client = boto3.client("sns", region_name=REGION)

def test_email_lambda():
    """Prueba la función Lambda de email directamente"""
    function_name = f"{SERVICE_NAME}-{STAGE}-sendEmailNotification"
    
    # Datos de prueba
    test_event = {
        "incident": {
            "incident_id": "test-123",
            "tipo": "EMERGENCIA",
            "descripcion": "Prueba de notificación por email",
            "ubicacion": {"edificio": "Edificio 1", "piso": 1},
            "urgencia": "ALTA",
            "created_at": "2024-01-01T00:00:00"
        },
        "reporter_email": "test@utec.edu.pe"
    }
    
    print(f"Probando función Lambda: {function_name}")
    print(f"Evento de prueba: {json.dumps(test_event, indent=2)}")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",  # Síncrono para ver el resultado
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response["Payload"].read())
        print(f"\nResultado: {json.dumps(result, indent=2)}")
        
        if result.get("statusCode") == 200:
            print("✅ Email enviado exitosamente")
        else:
            print(f"❌ Error: {result.get('body')}")
            
    except Exception as e:
        print(f"❌ Error invocando Lambda: {e}")

def check_sns_topic():
    """Verifica que el Topic SNS existe y tiene suscripciones"""
    topic_name = f"{SERVICE_NAME}-incident-notifications-{STAGE}"
    
    print(f"\nBuscando Topic SNS: {topic_name}")
    
    try:
        # Listar todos los topics
        topics = sns_client.list_topics()
        
        topic_arn = None
        for topic in topics.get("Topics", []):
            if topic_name in topic["TopicArn"]:
                topic_arn = topic["TopicArn"]
                break
        
        if not topic_arn:
            print(f"❌ No se encontró el topic: {topic_name}")
            print("💡 Asegúrate de haber desplegado el backend con: serverless deploy")
            return
        
        print(f"✅ Topic encontrado: {topic_arn}")
        
        # Verificar suscripciones
        subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
        subs = subscriptions.get("Subscriptions", [])
        
        print(f"\nSuscripciones encontradas: {len(subs)}")
        for sub in subs:
            status = sub.get("SubscriptionArn", "Pendiente")
            endpoint = sub.get("Endpoint", "N/A")
            protocol = sub.get("Protocol", "N/A")
            
            if "PendingConfirmation" in status or status == "PendingConfirmation":
                print(f"  ⚠️  {protocol}: {endpoint} - PENDIENTE DE CONFIRMACIÓN")
                print(f"     → Revisa tu correo y confirma la suscripción")
            elif status != "PendingConfirmation":
                print(f"  ✅ {protocol}: {endpoint} - CONFIRMADA")
            else:
                print(f"  ❓ {protocol}: {endpoint} - {status}")
        
        return topic_arn
        
    except Exception as e:
        print(f"❌ Error verificando SNS: {e}")

def check_lambda_config():
    """Verifica la configuración de la Lambda"""
    function_name = f"{SERVICE_NAME}-{STAGE}-sendEmailNotification"
    
    print(f"\nVerificando configuración de Lambda: {function_name}")
    
    try:
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        env_vars = config.get("Environment", {}).get("Variables", {})
        
        print(f"Variables de entorno:")
        print(f"  STAGE: {env_vars.get('STAGE', 'NO CONFIGURADO')}")
        print(f"  SERVICE_NAME: {env_vars.get('SERVICE_NAME', 'NO CONFIGURADO')}")
        print(f"  SNS_TOPIC_ARN: {env_vars.get('SNS_TOPIC_ARN', 'NO CONFIGURADO')}")
        
        if not env_vars.get("SNS_TOPIC_ARN"):
            print("❌ SNS_TOPIC_ARN no está configurado en la Lambda")
            print("💡 Ejecuta: serverless deploy para actualizar la configuración")
        else:
            print("✅ SNS_TOPIC_ARN configurado correctamente")
            
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"❌ La función Lambda {function_name} no existe")
        print("💡 Ejecuta: serverless deploy para crear la función")
    except Exception as e:
        print(f"❌ Error verificando Lambda: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("DIAGNÓSTICO DE NOTIFICACIONES POR EMAIL")
    print("=" * 60)
    
    check_lambda_config()
    topic_arn = check_sns_topic()
    
    print("\n" + "=" * 60)
    print("PRUEBA DE ENVÍO DE EMAIL")
    print("=" * 60)
    
    respuesta = input("\n¿Deseas probar el envío de email? (s/n): ")
    if respuesta.lower() == 's':
        test_email_lambda()
    else:
        print("Prueba cancelada. Para probar manualmente:")
        print(f"  python test_email_notification.py")

