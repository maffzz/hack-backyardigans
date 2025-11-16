import boto3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    try:
        body = event.get("body", {})
        if isinstance(body, str):
            import json
            body = json.loads(body)
        
        user_id = body.get("user_id")
        password = body.get("password")
        role = body.get("role")
        department = body.get("department")
        
        if not user_id or not password or not role:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Invalid request body: missing user_id or password'
                }
            }
        
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table("Users")
        
        table.put_item(Item={
            "user_id": user_id,
            "password": hash_password(password),
            "role": role,
            "department": department if department else None
        })
        
        return {
            'statusCode': 200,
            'body': {
                'message': 'User registered successfully',
                'user_id': user_id
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }