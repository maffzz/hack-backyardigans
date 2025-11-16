import os

def handler(event, context):
    # Obtener WS_ENDPOINT de variables de entorno
    ws_endpoint = os.environ.get("WS_ENDPOINT", "")
    # Convertir https:// a wss:// si es necesario
    ws_url = ws_endpoint.replace("https://", "wss://") if ws_endpoint else None
    
    return {
        'statusCode': 200,
        'body': {
            'status': 'healthy',
            'message': 'AlertaUTEC Backend is running!',
            'websocket': ws_url or 'Not configured'
        }
    }
