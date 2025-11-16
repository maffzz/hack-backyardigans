import boto3
from datetime import datetime

def lambda_handler(event, context):
    try:
        # Puede venir como dict directo o dentro de body
        if isinstance(event, dict) and "token" in event:
            token = event.get("token")
        elif isinstance(event, dict) and "body" in event:
            body = event.get("body")
            if isinstance(body, str):
                import json
                body = json.loads(body)
            token = body.get("token")
        else:
            token = event.get("token")
        
        if not token:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Token requerido'
                }
            }
        
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table("Tokens")
        
        res = table.get_item(Key={"token": token})
        
        if "Item" not in res:
            return {
                'statusCode': 403,
                'body': {
                    'error': 'Token no existe'
                }
            }
        
        item = res['Item']
        expires = item['expires']
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        if now > expires:
            return {
                'statusCode': 403,
                'body': {
                    'error': 'Token expirado'
                }
            }
        
        return {
            'statusCode': 200,
            'body': {
                "user_id": item["user_id"],
                "role": item["role"].lower(),
                "department": item.get("department")
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }