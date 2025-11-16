import boto3
import hashlib
import re

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_utec_email(email):
    if not email:
        return False, "Email es requerido"
    
    # Pattern para validar email UTEC
    pattern = r'^[a-zA-Z0-9._-]+@utec\.edu\.pe$'
    
    if not re.match(pattern, email):
        return False, "Debe usar un correo institucional válido (@utec.edu.pe)"
    
    return True, None

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
        
        # Validar campos requeridos
        if not user_id or not password or not role:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'user_id, password y role son requeridos'
                }
            }
        
        # VALIDACIÓN UTEC: Verificar que sea email institucional
        is_valid, error_msg = validate_utec_email(user_id)
        if not is_valid:
            return {
                'statusCode': 400,
                'body': {
                    'error': error_msg,
                    'hint': 'Ejemplo válido: juan.perez@utec.edu.pe'
                }
            }
        
        # Validar rol
        valid_roles = ["student", "staff", "admin"]
        if role.lower() not in valid_roles:
            return {
                'statusCode': 400,
                'body': {
                    'error': f'Rol inválido. Roles permitidos: {", ".join(valid_roles)}'
                }
            }
        
        # Si es staff, validar que tenga departamento
        if role.lower() == "staff" and not department:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'El rol staff requiere especificar un departamento'
                }
            }
        
        # Verificar si el usuario ya existe
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table("Users")
        
        existing_user = table.get_item(Key={"user_id": user_id})
        if "Item" in existing_user:
            return {
                'statusCode': 409,
                'body': {
                    'error': 'Este correo ya está registrado en el sistema'
                }
            }
        
        # Registrar usuario
        table.put_item(Item={
            "user_id": user_id,
            "password": hash_password(password),
            "role": role.lower(),
            "department": department if department else None,
            "created_at": __import__('datetime').datetime.utcnow().isoformat()
        })
        
        return {
            'statusCode': 200,
            'body': {
                'message': 'Usuario registrado exitosamente',
                'user_id': user_id,
                'role': role.lower()
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': {
                'error': 'Error interno del servidor',
                'detail': str(e)
            }
        }