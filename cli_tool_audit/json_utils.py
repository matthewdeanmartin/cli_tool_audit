"""
JSON utility functions.
"""

import dataclasses
import enum
from datetime import date, datetime
from typing import Any


def custom_json_serializer(o: Any) -> Any:
    """
    Custom JSON serializer for objects not serializable by default json code.

    Args:
        o (Any): The object to serialize.

    Returns:
        Any: A JSON serializable representation of the object.

    Raises:
        TypeError: If the object is not serializable.
    """
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if dataclasses.is_dataclass(o):
        return dataclasses.asdict(o)  # type: ignore
    if isinstance(o, enum.Enum):
        return o.value
    # Development time
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")
    # Production time
    # return str(o)


# def json_to_enum(cls, json_obj):
#     if isinstance(json_obj, dict):
#         for key, value in json_obj.items():
#             if isinstance(value, str) and key == 'schema':
#                 json_obj[key] = SchemaType(value)
#     return cls(**json_obj)
