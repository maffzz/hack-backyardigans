import json
from decimal import Decimal

def decimal_default(obj):
    """Convierte Decimal a float para JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def response(code, body):
    """
    Formatea la respuesta para Lambda con integration: lambda.
    Convierte el body a string JSON y maneja tipos Decimal de DynamoDB.
    """
    if isinstance(body, dict):
        body_str = json.dumps(body, default=decimal_default)
    elif isinstance(body, str):
        body_str = body
    else:
        body_str = json.dumps({"error": str(body)}, default=decimal_default)
    
    return {
        "statusCode": code,
        "body": body_str
    }

