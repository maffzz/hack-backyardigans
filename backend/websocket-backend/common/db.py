import os
import boto3
from typing import List, Dict, Optional

DYNAMO_TABLE = os.environ.get("CONNECTIONS_TABLE", "ws-connections")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMO_TABLE)

def save_connection(connection_id: str, user_id: Optional[str] = None) -> None:
    item: Dict[str, str] = {"connectionId": connection_id}
    if user_id:
        item["userId"] = user_id
    table.put_item(Item=item)

def delete_connection(connection_id: str) -> None:
    table.delete_item(Key={"connectionId": connection_id})

def list_connections() -> List[Dict]:
    resp = table.scan()
    return resp.get("Items", [])


def get_user_connections(user_id: str) -> List[Dict]:
    # versión simple: filtra en memoria.
    # si luego necesitas performance, puedes crear un índice GSI
    items = list_connections()
    return [i for i in items if i.get("userId") == user_id]