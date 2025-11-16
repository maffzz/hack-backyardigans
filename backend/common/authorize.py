import json
import boto3

def authorize(event):
    token = event["headers"].get("Authorization")

    if not token:
        return None

    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(
        FunctionName="alertautec-backend-dev-ValidarTokenAcceso",
        InvocationType="RequestResponse",
        Payload=json.dumps({"token": token})
    )

    payload = json.loads(response["Payload"].read())

    if payload["statusCode"] == 403:
        return None

    return json.loads(payload["body"])
