from common.locations import get_valid_locations

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
        
        return {
            'statusCode': 200,
            'body': {
                'locations': formatted_locations
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
