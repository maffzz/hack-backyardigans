import json
import boto3
import jwt
from datetime import datetime

# Secret key for JWT signing - in production, use environment variable
JWT_SECRET = "alertautec-secret-key-2024"

def generate_jwt_token(user_data):
    """Generate a JWT token for authenticated user"""
    payload = {
        "user_id": user_data["user_id"],
        "role": user_data["role"],
        "department": user_data.get("department"),
        "email": user_data.get("email"),
        "name": user_data.get("name", ""),
        "exp": datetime.utcnow().timestamp() + 28800  # 8 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def validate_jwt_token(token):
    """Validate JWT token and return user data"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_from_request(event):
    """Extract and validate user from request using JWT token"""
    # Try Authorization header first
    auth_header = event.get("headers", {}).get("Authorization")
    if not auth_header:
        # Try query parameters
        auth_header = event.get("queryStringParameters", {}).get("token")
    
    if not auth_header:
        return None
    
    # Remove "Bearer " prefix if present
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = auth_header
    
    # Validate JWT token
    user_data = validate_jwt_token(token)
    if not user_data:
        return None
    
    return user_data

def require_role(allowed_roles):
    """Decorator to require specific user roles"""
    def decorator(func):
        def wrapper(event, context):
            user = get_user_from_request(event)
            if not user:
                return {
                    "statusCode": 401,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "No autorizado - token inválido"})
                }
            
            if user.get("role") not in allowed_roles:
                return {
                    "statusCode": 403,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Prohibido - rol no autorizado"})
                }
            
            # Add user to event for downstream use
            event["user"] = user
            return func(event, context)
        return wrapper
    return decorator

def require_auth(func):
    """Decorator to require authentication"""
    return require_role(["student", "staff", "authority"])(func)
