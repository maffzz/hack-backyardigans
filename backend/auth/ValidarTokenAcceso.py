import boto3
from datetime import datetime

def lambda_handler(event, context):
    body = event.get("body", {})
    token = body.get('token')
    
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("Tokens")
    
    res = table.get_item(Key={"token": token})
    
    if "Item" not in res:
        return {
            'statusCode': 403,
            'body': 'Token no existe'
        }
    else:
        item = res['Item']
        expires = item['expires']
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        if now > expires:
            return {
                'statusCode': 403,
                'body': 'Token expirado'
            }
        
        return {
            'statusCode': 200,
            'body': {
                "user_id": item["user_id"],
                "role": item["role"],
                "department": item.get("department")
            }
        }