import json
from decimal import Decimal

def decimal_default(obj):
    """Convierte Decimal a float para JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def response(code, body):
    """
    Formatea la respuesta para Lambda con lambda-proxy (más simple).
    Devuelve el body como objeto JSON directamente, no como string.
    """
    # Convertir body a dict si es necesario, manejando Decimal
    if isinstance(body, dict):
        # Serializar y parsear para convertir Decimal a float
        body_json = json.dumps(body, default=decimal_default)
        body_dict = json.loads(body_json)
    elif isinstance(body, str):
        try:
            body_dict = json.loads(body)
        except:
            body_dict = {"error": body}
    else:
        body_dict = {"error": str(body)}
    
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body_dict, default=decimal_default)
    }

