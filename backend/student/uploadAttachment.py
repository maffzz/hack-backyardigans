import json
import os
import boto3
import base64
import uuid
import traceback
from common.response import response

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Incidentes")

BUCKET = os.environ.get("S3_BUCKET", "alertautec-attachments")

def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        incident_id = path_params.get("id")
        if not incident_id:
            return response(400, {"error": "ID de incidente requerido"})

        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)


        if "file" not in body or "filename" not in body:
            return response(400, {"error": "Falta file o filename"})

        file_data = base64.b64decode(body["file"])
        filename = f"{incident_id}/{uuid.uuid4()}_{body['filename']}"

        s3.put_object(
            Bucket=BUCKET,
            Key=filename,
            Body=file_data
        )

        # Construir URL del archivo en S3
        region = os.environ.get('AWS_REGION', 'us-east-1')
        if region == 'us-east-1':
            file_url = f"https://{BUCKET}.s3.amazonaws.com/{filename}"
        else:
            file_url = f"https://{BUCKET}.s3.{region}.amazonaws.com/{filename}"

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
