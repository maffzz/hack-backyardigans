import json
import os
import boto3
from common.authorize import authorize

# DynamoDB y SageMaker Runtime
DYNAMODB = boto3.resource("dynamodb")
INCIDENTS_TABLE = DYNAMODB.Table("Incidentes")
RUNTIME = boto3.client(
    "sagemaker-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
)

# Nombre del endpoint de SageMaker que sugiere el departamento
SUGGEST_DEPT_ENDPOINT = os.environ.get(
    "SUGGEST_DEPT_ENDPOINT",
    "alertautec-suggest-department",
)


def _build_incident_payload(incident: dict) -> dict:
    """Extrae solo los campos relevantes para el modelo."""
    if not incident:
        return {}

    return {
        "tipo": incident.get("tipo"),
        "descripcion": incident.get("descripcion"),
        "urgencia": incident.get("urgencia"),
        "ubicacion": incident.get("ubicacion"),
    }


def handler(event, context):
    try:
        # Autorizar usuario
        user = authorize(event)
        if not user:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Token inválido"}),
            }

        # Solo staff y admin pueden pedir sugerencias
        if user["role"] not in ["staff", "admin"]:
            return {
                "statusCode": 403,
                "body": json.dumps({
                    "error": "Solo staff y administradores pueden usar este endpoint",
                }),
            }

        # Leer incident_id desde pathParameters: /staff/incidents/{id}/suggest-department
        path_params = event.get("pathParameters") or {}
        incident_id = path_params.get("id")

        if not incident_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "ID de incidente requerido"}),
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

        # Preparar payload para SageMaker
        payload = _build_incident_payload(incident)

        # Invocar endpoint de SageMaker
        sm_response = RUNTIME.invoke_endpoint(
            EndpointName=SUGGEST_DEPT_ENDPOINT,
            ContentType="application/json",
            Body=json.dumps(payload),
        )

        raw = sm_response["Body"].read().decode("utf-8")
        try:
            suggestion = json.loads(raw)
        except Exception:
            suggestion = {"raw_response": raw}

        # Importante: NO actualizamos DynamoDB, solo devolvemos sugerencia
        return {
            "statusCode": 200,
            "body": json.dumps({
                "incident_id": incident_id,
                "input": payload,
                "suggestion": suggestion,
            }),
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error al sugerir departamento",
                "detail": str(e),
            }),
        }