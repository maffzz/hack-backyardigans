import json

def response(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": body
    }

VALID = {
    "1": list(range(1, 12)),  
    "2": [1, 2]             
}

def handler(event, context):
    try:
        body = event.get("body")

        edificio = body.get("edificio")
        piso = body.get("piso")

        if edificio not in VALID:
            return response(400, {"valid": False, "error": "Edificio no existe"})

        if piso not in VALID[edificio]:
            return response(400, {"valid": False, "error": "Piso inválido"})

        return response(200, {"valid": True})

    except Exception as e:
        return response(500, {"error": str(e)})
