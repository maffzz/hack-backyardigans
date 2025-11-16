import json
import boto3
import traceback
from decimal import Decimal
from common.authorize import authorize

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def decimal_default(obj):
    """Convierte Decimal a float para JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def response(code, body):
    if isinstance(body, dict):
        body_str = json.dumps(body, default=decimal_default)
    elif isinstance(body, str):
        body_str = body
    else:
        body_str = json.dumps({"error": str(body)}, default=decimal_default)
    
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": body_str
    }

def handler(event, context):
    try:
        user = authorize(event)
        if not user:
            return response(403, {"error": "Token inválido"})     

        incident_id = event["pathParameters"]["id"]

        result = table.get_item(Key={"incident_id": incident_id})  

        if "Item" not in result:
            return response(404, {"error": "Incidente no encontrado"})
                                                                
        return response(200, {"data": result["Item"]})

    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": str(e)})
