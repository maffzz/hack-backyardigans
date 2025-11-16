import json
from common.locations import get_valid_locations

def response(code, body):
    if isinstance(body, dict):
        body_str = json.dumps(body)
    elif isinstance(body, str):
        body_str = body
    else:
        body_str = json.dumps({"error": str(body)})
    
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
        locations = get_valid_locations()
        
        # Formatear para el frontend
        formatted_locations = []
        for location_id, location_data in locations.items():
            formatted_locations.append({
                "id": location_id,
                "nombre": location_data.get("nombre", location_id),
                "pisos": location_data.get("pisos", []),
                "descripcion": location_data.get("descripcion", ""),
                "coordenadas": location_data.get("coordenadas", {})
            })
        
        return response(200, {
            "locations": formatted_locations
        })
    except Exception as e:
        return response(500, {"error": str(e)})
