import json

def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "status": "healthy",
            "message": "AlertaUTEC Backend is running!",
            "websocket": "wss://22iontuw79.execute-api.us-east-1.amazonaws.com/dev"
        })
    }
