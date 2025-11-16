import boto3
import traceback
from common.response import response
from common.authorize import authorize

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

def handler(event, context):
    try:
        user = authorize(event)
        if not user:
            return response(403, {"error": "Token inválido"})

        path_params = event.get("pathParameters") or {}
        incident_id = path_params.get("id")
        
        if not incident_id:
            return response(400, {"error": "ID de incidente requerido"})

        result = table.get_item(Key={"incident_id": incident_id})

        if "Item" not in result:
            return response(404, {"error": "Incidente no encontrado"})

        return response(200, {"data": result["Item"]})

    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": str(e)})