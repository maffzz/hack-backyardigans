import json
from common.auth import validate_jwt_token

def lambda_handler(event, context):
    token = event.get("token")

    if not token:
        return {"statusCode": 403, "body": "Token no proporcionado"}

    # Validate JWT token
    user_data = validate_jwt_token(token)
    
    if not user_data:
        return {"statusCode": 403, "body": "Token inválido o expirado"}       

    return {
        "statusCode": 200,
        "body": json.dumps({
            "user_id": user_data["user_id"],
            "role": user_data["role"],
            "department": user_data.get("department"),
            "email": user_data.get("email"),
            "name": user_data.get("name", "")
        })
    }
