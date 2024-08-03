import dataclasses
import enum
from datetime import date, datetime
from unittest.mock import Mock

import pytest

from cli_tool_audit.json_utils import custom_json_serializer

# I'll start by examining the code and looking for any potential bugs:
#
# 1. The `custom_json_serializer` function handles serialization of certain types
#    to JSON but raises a `TypeError` at development time. It might be better to
#    return a default str representation of the object at that time to provide
#    more information during testing and debugging.
# 2. The commented-out `json_to_enum` function is not currently in use. It might
#    be a leftover or incomplete code. We should remove it or complete it if
#    necessary.
# 3. There is a slight typo in the module's docstring where "json" is mistakenly
#    spelled as "jon".
#
# I will now proceed to write pytest unit tests for the `custom_json_serializer`
# function covering different scenarios.


def test_custom_json_serializer_datetime():
    # Test datetime serialization
    test_datetime = datetime(2022, 2, 8, 12, 30, 45)
    assert custom_json_serializer(test_datetime) == test_datetime.isoformat()


def test_custom_json_serializer_date():
    # Test date serialization
    test_date = date(2022, 2, 8)
    assert custom_json_serializer(test_date) == test_date.isoformat()


def test_custom_json_serializer_dataclass():
    # Test dataclass serialization
    @dataclasses.dataclass
    class Person:
        name: str
        age: int

    test_person = Person(name="Alice", age=30)
    assert custom_json_serializer(test_person) == {"name": "Alice", "age": 30}


def test_custom_json_serializer_enum():
    # Test enum serialization
    class Color(enum.Enum):
        RED = "Red"
        BLUE = "Blue"

    assert custom_json_serializer(Color.RED) == "Red"


def test_custom_json_serializer_unknown():
    # Test serialization of an unknown object type
    unknown_object = Mock()
    with pytest.raises(TypeError):
        custom_json_serializer(unknown_object)


# Optionally, test the production implementation by uncommenting the following test
# def test_custom_json_serializer_production():
#     assert custom_json_serializer("test") == "test"  # Replace with the expected production behavior

# No more unit tests

# These tests cover the serialization of `datetime`, `date`, dataclasses, and
# enums using the `custom_json_serializer` function. Additionally, there is a test
# for an unknown object type to ensure the correct handling of such cases.
