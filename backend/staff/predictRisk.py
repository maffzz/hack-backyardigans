import json
import boto3
import os
from datetime import datetime
from common.authorize import authorize  # ya existe en tu backend

runtime = boto3.client("sagemaker-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
ENDPOINT_NAME = os.environ.get("RISK_MODEL_ENDPOINT", "alertautec-risk-model-dev")

def handler(event, context):
    try:
        # 1) Autorizar usuario (mismo mecanismo que staff/*)
        user = authorize(event)
        if not user:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Token inválido"})
            }

        # Solo staff y admin
        if user["role"] not in ["staff", "admin"]:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Solo staff y administradores pueden usar este endpoint"})
            }

        # 2) Leer cuerpo
        body = event.get("body") or {}
        if isinstance(body, str):
            body = json.loads(body)

        edificio = body.get("edificio")
        piso = body.get("piso")
        urgencia = body.get("urgencia")
        hora = body.get("hora")
        dia_semana = body.get("dia_semana")

        now = datetime.utcnow()
        if hora is None:
            hora = now.hour
        if dia_semana is None:
            dia_semana = now.weekday()

        if not edificio or piso is None or not urgencia:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Faltan campos requeridos: edificio, piso, urgencia"
                })
            }

        features = {
            "edificio": edificio,
            "piso": piso,
            "hora": hora,
            "dia_semana": dia_semana,
            "urgencia": urgencia
        }

        # 3) Invocar endpoint de SageMaker
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Body=json.dumps(features),
        )

        raw = response["Body"].read().decode("utf-8")
        try:
            pred = json.loads(raw)
        except Exception:
            pred = {"raw_prediction": raw}

        return {
            "statusCode": 200,
            "body": json.dumps({
                "input": features,
                "prediction": pred
            })
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error invocando modelo de riesgo",
                "detail": str(e)
            })
        }