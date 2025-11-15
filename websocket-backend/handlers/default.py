import os
import json
import boto3
from common.db import list_connections, delete_connection

WS_ENDPOINT = os.environ.get("WS_ENDPOINT")  # ej: https://abc123.execute-api.us-east-1.amazonaws.com/dev

apigw = boto3.client("apigatewaymanagementapi", endpoint_url=WS_ENDPOINT)

def _post_to_connection(connection_id: str, payload: dict) -> None:
    data_bytes = json.dumps(payload).encode("utf-8")
    try:
        apigw.post_to_connection(ConnectionId=connection_id, Data=data_bytes)
    except apigw.exceptions.GoneException:
        # conexión muerta → la eliminamos
        delete_connection(connection_id)
    except Exception as e:
        # en hackatón basta con loguear
        print(f"Error enviando a {connection_id}: {e}")

def handler(event, context):
    """
    lambda para la ruta $default
    maneja mensajes entrantes y decide qué hacer
    """
    connection_id = event["requestContext"]["connectionId"]
    raw_body = event.get("body") or ""

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        body = {}

    action = body.get("action", "echo")
    message = body.get("message", "")

    if action == "ping":
        # respuesta simple para health-check
        _post_to_connection(connection_id, {"type": "pong"})
    elif action == "echo":
        # reenvía solo al mismo cliente
        _post_to_connection(connection_id, {"type": "echo", "message": message})
    elif action == "broadcast":
        # envía a TODOS los conectados
        conns = list_connections()
        payload = {"type": "broadcast", "message": message}
        for c in conns:
            _post_to_connection(c["connectionId"], payload)
    else:
        # acción no reconocida
        _post_to_connection(connection_id, {
            "type": "error",
            "error": f"Unknown action: {action}",
        })

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "ok"}),
    }