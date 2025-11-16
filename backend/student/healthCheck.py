def handler(event, context):
    return {
        'statusCode': 200,
        'body': {
            'status': 'healthy',
            'message': 'AlertaUTEC Backend is running!',
            'websocket': 'wss://22iontuw79.execute-api.us-east-1.amazonaws.com/dev'
        }
    }
