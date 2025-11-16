import json
import boto3
import traceback
from common.response import response
from common.authorize import authorize
from common.database import DatabaseHelper

def handler(event, context):
    try:
        user = authorize(event)
        if not user:
            return response(403, {"error": "Token inválido"})

        if user["role"] not in ["staff", "admin"]:
            return response(403, {"error": "Permiso denegado"})

        
        path_params = event.get("pathParameters") or {}
        incident_id = path_params.get("id")
        if not incident_id:
            return response(400, {"error": "ID de incidente requerido"})
        
        # Parámetros de paginación
        query_params = event.get("queryStringParameters") or {}
        limit = int(query_params.get("limit", 50))
        last_key = query_params.get("lastKey")
        
        # Usar paginación optimizada para eventos
        result = DatabaseHelper.get_incident_events_paginated(
            incident_id,
            limit=limit,
            last_evaluated_key=json.loads(last_key) if last_key else None
        )
        
        response_data = {
            "data": result["items"],
            "pagination": {
                "nextKey": result["last_evaluated_key"] if result["last_evaluated_key"] else None,
                "limit": limit,
                "hasMore": result["last_evaluated_key"] is not None,
                "count": result["count"]
            }
        }
        
        return response(200, response_data)
    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": "Error interno"})
