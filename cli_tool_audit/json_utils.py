"""
JSON utility functions.
"""
from datetime import date, datetime
from typing import Any


def custom_json_serializer(o: Any) -> str:
    """
    Custom JSON serializer for objects not serializable by default json code.

    Args:
        o (Any): The object to serialize.

    Returns:
        str: A JSON serializable representation of the object.
    """
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    return str(o)
