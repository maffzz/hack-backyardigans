VALID_LOCATIONS = {
    "1": {
        "nombre": "Edificio 1",
        "pisos": list(range(1, 12)),
        "descripcion": "Edificio principal",
        "coordenadas": {}
    },
    "2": {
        "nombre": "Edificio 2",
        "pisos": [1, 2],
        "descripcion": "Edificio secundario",
        "coordenadas": {}
    }
}

def get_valid_locations():
    return VALID_LOCATIONS

