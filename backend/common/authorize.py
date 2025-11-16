import json
import os
import boto3

# Obtener nombre de la función Lambda desde variables de entorno
VALIDATE_TOKEN_LAMBDA = os.environ.get(
    "VALIDATE_TOKEN_LAMBDA",
    f"{os.environ.get('SERVICE_NAME', 'alertautec-backend')}-{os.environ.get('STAGE', 'dev')}-ValidarTokenAcceso"
)

def authorize(event):
    headers = event.get("headers", {})
    token = headers.get("Authorization") or headers.get("authorization")
    
    if not token:
        return None
    
    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(
        FunctionName=VALIDATE_TOKEN_LAMBDA,
        InvocationType="RequestResponse",
        Payload=json.dumps({"body": {"token": token}})
    )
    
    payload = json.loads(response["Payload"].read())
        
    if payload.get("statusCode") == 403:
        return None
    
    body = payload.get("body")
    
    return body