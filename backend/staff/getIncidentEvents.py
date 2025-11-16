import json
import boto3
import traceback
from common.authorize import authorize
from common.database import DatabaseHelper
from common.helpers import convert_decimals

def handler(event, context):
    try:
        user = authorize(event)
        if not user:
            return {
                'statusCode': 403,
                'body': json.dumps({
                    'error': 'Token inválido'
                })
            }

        if user["role"] not in ["staff", "admin"]:
            return {
                'statusCode': 403,
                'body': json.dumps({
                    'error': 'Permiso denegado'
                })
            }

        path_params = event.get("pathParameters") or {}
        incident_id = path_params.get("id")
        if not incident_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'ID de incidente requerido'
                })
            }
        
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
        
        items = convert_decimals(result["items"])
        
        response_data = {
            "data": items,
            "pagination": {
                "nextKey": result["last_evaluated_key"] if result["last_evaluated_key"] else None,
                "limit": limit,
                "hasMore": result["last_evaluated_key"] is not None,
                "count": result["count"]
            }
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Error interno'
            })
        }
