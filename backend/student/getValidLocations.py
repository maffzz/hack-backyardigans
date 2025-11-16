from common.response import response
from common.locations import get_valid_locations
from common.authorize import authorize

def handler(event, context):
    try:
        user = authorize(event)
        if not user:
            return response(403, {"error": "Token inválido"})
        
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
