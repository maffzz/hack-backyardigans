import json
from common.db import delete_connection

def handler(event, context):
    """
    lambda para la ruta $disconnect
    elimina el connectionId de la tabla
    """
    connection_id = event["requestContext"]["connectionId"]
    delete_connection(connection_id)

    return {
        "statusCode": 200,
        "body": {"message": "Disconnected", "connectionId": connection_id},
    }