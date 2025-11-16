import boto3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    try:
        user_id = event.get("user_id")
        password = event.get("password")
        role = event.get("role")
        department = event.get("department")

        if not user_id or not password or not role:
            message = {
                'error': 'Invalid request body: missing user_id or password'
            }
            return {
                'statusCode': 400,
                'body': message
            }

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table("Users")

        table.put_item(Item={
            "user_id": user_id,
            "password": hash_password(password),
            "role": role,
            "department": department if department else None
        })

        message = {
            'message': 'User registered successfully',
            'user_id': user_id
        }
        return {
            'statusCode': 200,
            'body': message
        }

    except Exception as e:
        message = {
            'error': str(e)
        }        
        return {
            'statusCode': 500,
            'body': message
        }