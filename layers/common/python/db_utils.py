"""Thin DynamoDB helpers — keep Lambda code clean and consistent."""

from typing import Any, Dict, List, Optional

from boto3.dynamodb.conditions import Key


def put_item(table: Any, item: Dict) -> Dict:
    table.put_item(Item=item)
    return item


def get_item(table: Any, key: Dict) -> Optional[Dict]:
    resp = table.get_item(Key=key)
    return resp.get("Item")


def query_by_partition(
    table: Any,
    pk_name: str,
    pk_value: str,
    limit: int = 50,
    scan_forward: bool = False,
) -> List[Dict]:
    resp = table.query(
        KeyConditionExpression=Key(pk_name).eq(pk_value),
        Limit=limit,
        ScanIndexForward=scan_forward,
    )
    return resp.get("Items", [])


def query_gsi(
    table: Any,
    index_name: str,
    pk_name: str,
    pk_value: str,
    limit: int = 50,
    scan_forward: bool = False,
) -> List[Dict]:
    resp = table.query(
        IndexName=index_name,
        KeyConditionExpression=Key(pk_name).eq(pk_value),
        Limit=limit,
        ScanIndexForward=scan_forward,
    )
    return resp.get("Items", [])


def delete_item(table: Any, key: Dict) -> None:
    table.delete_item(Key=key)


def update_counter(table: Any, key: Dict, attr: str, delta: int = 1) -> None:
    """Atomically increment/decrement a numeric attribute."""
    table.update_item(
        Key=key,
        UpdateExpression=f"ADD {attr} :d",
        ExpressionAttributeValues={":d": delta},
    )
