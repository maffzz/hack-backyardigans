import json

VALID = {
    "1": list(range(1, 12)),  
    "2": [1, 2]             
}

def handler(event, context):
    try:
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        edificio = body.get("edificio")
        piso = body.get("piso")

        if edificio not in VALID:
            return {
                'statusCode': 400,
                'body': {
                    'valid': False,
                    'error': 'Edificio no existe'
                }
            }

        if piso not in VALID[edificio]:
            return {
                'statusCode': 400,
                'body': {
                    'valid': False,
                    'error': 'Piso inválido'
                }
            }

        return {
            'statusCode': 200,
            'body': {
                'valid': True
            }
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
