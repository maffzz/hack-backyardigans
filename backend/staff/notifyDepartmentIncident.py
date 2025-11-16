import json
import boto3
import traceback

# Tablas y recursos
DYNAMODB = boto3.resource("dynamodb")
INCIDENTS_TABLE = DYNAMODB.Table("Incidentes")
S3 = boto3.client("s3")


def _parse_event(event):
    """Admite evento directo (dict) o con body JSON (por compatibilidad futura)."""
    if not event:
        return {}

    # Si viene desde API Gateway, el payload suele ir en body
    body = event.get("body") if isinstance(event, dict) else None
    if body:
        if isinstance(body, str):
            try:
                return json.loads(body)
            except Exception:
                return {}
        if isinstance(body, dict):
            return body

    # Caso simple: Airflow invoca pasando el payload directo
    if isinstance(event, dict):
        return event

    return {}


def handler(event, context):
    try:
        payload = _parse_event(event)

        incident_id = payload.get("incident_id")
        departamento = payload.get("departamento")
        s3_bucket = payload.get("s3_bucket")
        s3_key = payload.get("s3_key")

        missing = [k for k in ["incident_id", "departamento", "s3_bucket", "s3_key"] if not payload.get(k)]
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

        # Verificar que el objeto en S3 exista (opcional, pero útil para validar)
        try:
            S3.head_object(Bucket=s3_bucket, Key=s3_key)
            s3_exists = True
        except Exception:
            s3_exists = False

        # Por ahora solo registramos en logs; más adelante aquí se integraría SES/SNS
        print(
            f"Notificación a departamento '{departamento}' para incidente '{incident_id}'. "
            f"Reporte en s3://{s3_bucket}/{s3_key}, existe={s3_exists}"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Notificación de incidente para departamento procesada",
                "incident_id": incident_id,
                "departamento": departamento,
                "s3_bucket": s3_bucket,
                "s3_key": s3_key,
                "s3_exists": s3_exists,
            }),
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error interno al notificar incidente a departamento",
                "detail": str(e),
            }),
        }
