import json
import boto3
import base64
import uuid
import traceback

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

BUCKET = "BUCKET......"   

def response(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }

def handler(event, context):
    try:
        incident_id = event["pathParameters"]["id"]

        body = json.loads(event["body"])

        if "file" not in body or "filename" not in body:
            return response(400, {"error": "Falta file o filename"})

        file_data = base64.b64decode(body["file"])
        filename = f"{incident_id}/{uuid.uuid4()}_{body['filename']}"

        s3.put_object(
            Bucket=BUCKET,
            Key=filename,
            Body=file_data
        )

        file_url = f"https://{BUCKET}.s3.amazonaws.com/{filename}"

        table.update_item(
            Key={"incident_id": incident_id},
            UpdateExpression="SET evidencia_url = list_append(if_not_exists(evidencia_url, :empty), :val)",
            ExpressionAttributeValues={
                ":val": [file_url],
                ":empty": []
            }
        )

        return response(200, {"message": "Archivo subido", "url": file_url})

    except Exception as e:
        traceback.print_exc()
        return response(500, {"error": str(e)})
