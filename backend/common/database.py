import boto3
import json

dynamodb = boto3.resource("dynamodb")
events_table = dynamodb.Table("IncidenteEventos")

class DatabaseHelper:
    @staticmethod
    def get_incident_events_paginated(incident_id, limit=50, last_evaluated_key=None):
        try:
            query_params = {
                "KeyConditionExpression": "incident_id = :incident_id",
                "ExpressionAttributeValues": {":incident_id": incident_id},
                "Limit": limit,
                "ScanIndexForward": False  # Más recientes primero
            }
            
            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key
            
            result = events_table.query(**query_params)
            
            return {
                "items": result.get("Items", []),
                "last_evaluated_key": result.get("LastEvaluatedKey"),
                "count": len(result.get("Items", []))
            }
        except Exception as e:
            return {
                "items": [],
                "last_evaluated_key": None,
                "count": 0
            }

