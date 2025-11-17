import json
import boto3

def authorize(event):
    headers = event.get("headers", {})
    token = headers.get("Authorization") or headers.get("authorization")

    if not token:
        return None

    # Permitir formato "Bearer <token>" desde frontend
    if isinstance(token, str) and token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]
    
    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(
        FunctionName="alertautec-backend-dev-ValidarTokenAcceso",
        InvocationType="RequestResponse",
        Payload=json.dumps({"body": {"token": token}})
    )
    
    payload = json.loads(response["Payload"].read())
        
    if payload.get("statusCode") == 403:
        return None
    
    body = payload.get("body")
    
    return body