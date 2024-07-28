import dataclasses
import datetime
import enum

import pytest

from cli_tool_audit.json_utils import custom_json_serializer


# Sample dataclass for testing
@dataclasses.dataclass
class SampleDataClass:
    name: str
    value: int


# Sample enum for testing
class SampleEnum(enum.Enum):
    OPTION_A = "Option A"
    OPTION_B = "Option B"


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (datetime.datetime(2023, 1, 1, 12, 0, 0), "2023-01-01T12:00:00"),
        (datetime.date(2023, 1, 1), "2023-01-01"),
        (SampleDataClass(name="Test", value=123), {"name": "Test", "value": 123}),
        (SampleEnum.OPTION_A, "Option A"),
    ],
)
def test_custom_json_serializer_valid(input_value, expected_output):
    """Test that custom_json_serializer correctly serializes valid inputs."""
    result = custom_json_serializer(input_value)
    assert result == expected_output


@pytest.mark.parametrize(
    "input_value",
    [
        object(),  # Unrecognized object type
        "A string",  # A string is not serializable
        42,  # An integer is not serializable
    ],
)
def test_custom_json_serializer_invalid(input_value):
    """Test that custom_json_serializer raises TypeError for invalid inputs."""
    with pytest.raises(TypeError):
        custom_json_serializer(input_value)



# Example dataclass and enum for testing purposes
@dataclasses.dataclass
class ExampleDataClass:
    name: str
    value: int


class ExampleEnum(enum.Enum):
    VALUE_ONE = "value_one"
    VALUE_TWO = "value_two"


# Test suite for custom_json_serializer
def test_custom_json_serializer_date():
    test_date = datetime.date(2022, 1, 1)
    assert custom_json_serializer(test_date) == "2022-01-01"


def test_custom_json_serializer_datetime():
    test_datetime = datetime.datetime(2022, 1, 1, 12, 0, 0)
    assert custom_json_serializer(test_datetime) == "2022-01-01T12:00:00"


def test_custom_json_serializer_dataclass():
    test_instance = ExampleDataClass(name="example", value=42)
    assert custom_json_serializer(test_instance) == {"name": "example", "value": 42}


def test_custom_json_serializer_enum():
    assert custom_json_serializer(ExampleEnum.VALUE_ONE) == "value_one"


def test_custom_json_serializer_none():
    with pytest.raises(TypeError):
        custom_json_serializer(None)


def test_custom_json_serializer_int():
    with pytest.raises(TypeError):
        custom_json_serializer(123)


def test_custom_json_serializer_str():
    with pytest.raises(TypeError):
        custom_json_serializer("test string")


def test_custom_json_serializer_list():
    with pytest.raises(TypeError):
        custom_json_serializer([1, 2, 3])  # List is not supported


def test_custom_json_serializer_dict():
    with pytest.raises(TypeError):
        custom_json_serializer({"key": "value"})  # Dict is not supported
