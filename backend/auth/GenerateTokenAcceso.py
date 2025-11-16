import boto3
import hashlib
import uuid
from datetime import datetime, timedelta

# Hashear contraseña
def hash_password(password):
    # Retorna la contraseña hasheada
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    try:
        # Entrada (json)
        body = event.get('body', {})
        if isinstance(body, str):
            import json
            body = json.loads(body)
        
        user_id = body.get('user_id')
        password = body.get('password')
        
        # Validar campos requeridos
        if not user_id or not password:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'user_id y password requeridos'
                }
            }
        
        hashed_password = hash_password(password)
        
        # Proceso
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('Users')
        
        response = table.get_item(
            Key={
                'user_id': user_id
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 403,
                'body': {
                    'error': 'Usuario no existe'
                }
            }
        
        user = response['Item']
        hashed_password_bd = user['password']
        
        if hashed_password != hashed_password_bd:
            return {
                'statusCode': 403,
                'body': {
                    'error': 'Password incorrecto'
                }
            }
        
        # Genera token
        token = str(uuid.uuid4())
        fecha_hora_exp = datetime.utcnow() + timedelta(hours=8)
        
        registro = {
            'token': token,
            'user_id': user_id,
            'role': user.get('role', 'student'),
            'department': user.get('department'),
            'expires': fecha_hora_exp.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        table = dynamodb.Table('Tokens')
        table.put_item(Item=registro)
        
        # Salida (json)
        return {
            'statusCode': 200,
            'body': {
                'token': token,
                'role': user.get('role', 'student'),
                'department': user.get('department')
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