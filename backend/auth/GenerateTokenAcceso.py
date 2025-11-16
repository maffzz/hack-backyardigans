import boto3
import hashlib
import uuid
from datetime import datetime, timedelta

# Hashear contraseña
def hash_password(password):
    # Retorna la contraseña hasheada
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    # Entrada (json)
    user_id = event.get('user_id')
    password = event.get('password')
    
    # Validar campos requeridos
    if not user_id or not password:
        return {
            'statusCode': 400,
            'body': 'user_id y password requeridos'
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
            'body': 'Usuario no existe'
        }
    else:
        user = response['Item']
        hashed_password_bd = user['password']
        
        if hashed_password == hashed_password_bd:
            # Genera token
            token = str(uuid.uuid4())
            fecha_hora_exp = datetime.now() + timedelta(minutes=60)
            
            registro = {
                'token': token,
                'user_id': user_id,
                'role': user.get('role', 'student'),
                'department': user.get('department'),
                'expires': fecha_hora_exp.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            table = dynamodb.Table('Tokens')
            dynamodbResponse = table.put_item(Item=registro)
        else:
            return {
                'statusCode': 403,
                'body': 'Password incorrecto'
            }
    
    # Salida (json)
    return {
        'statusCode': 200,
        'token': token,
        'role': user.get('role', 'student'),
        'department': user.get('department')
    }
    