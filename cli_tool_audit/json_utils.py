"""
JSON utility functions.
"""
from datetime import date, datetime


def custom_json_serializer(o):
    """
    Custom JSON serializer for objects not serializable by default json code.

    Args:
        o (object): The object to serialize.

    Returns:
        str: A JSON serializable representation of the object.
    """
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    return str(o)
