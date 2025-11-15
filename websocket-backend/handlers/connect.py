import json
from common.db import save_connection

def handler(event, context):
    """
    lambda para la ruta $connect de API Gateway WebSocket
    guarda el connectionId (y opcionalmente un userId)
    """
    connection_id = event["requestContext"]["connectionId"]

    # Opcional: leer un userId de la query string ?userId=...
    user_id = None
    qs_params = event.get("queryStringParameters") or {}
    if "userId" in qs_params:
        user_id = qs_params["userId"]

    save_connection(connection_id, user_id=user_id)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Connected", "connectionId": connection_id}),
    }