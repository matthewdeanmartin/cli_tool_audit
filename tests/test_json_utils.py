"""Tests for cli_tool_audit.json_utils module."""

import json
from datetime import date, datetime

import pytest

from cli_tool_audit.json_utils import custom_json_serializer
from cli_tool_audit.models import CliToolConfig, SchemaType


def test_serializes_datetime():
    dt = datetime(2024, 3, 15, 12, 0, 0)
    result = custom_json_serializer(dt)
    assert result == "2024-03-15T12:00:00"


def test_serializes_date():
    d = date(2024, 3, 15)
    result = custom_json_serializer(d)
    assert result == "2024-03-15"


def test_serializes_dataclass():
    config = CliToolConfig(name="mytool", version="1.0.0")
    result = custom_json_serializer(config)
    assert isinstance(result, dict)
    assert result["name"] == "mytool"
    assert result["version"] == "1.0.0"


def test_serializes_enum():
    result = custom_json_serializer(SchemaType.SEMVER)
    assert result == "semver"

    result = custom_json_serializer(SchemaType.EXISTENCE)
    assert result == "existence"


def test_raises_on_unserializable_type():
    with pytest.raises(TypeError, match="not JSON serializable"):
        custom_json_serializer(object())


def test_serializer_works_in_json_dumps():
    config = CliToolConfig(name="tool", version="2.0.0", schema=SchemaType.PEP440)
    output = json.dumps(config, default=custom_json_serializer)
    parsed = json.loads(output)
    assert parsed["name"] == "tool"
    assert parsed["version"] == "2.0.0"
    assert parsed["schema"] == "pep440"


def test_serializer_handles_datetime_in_nested_dict():
    data = {"ts": datetime(2024, 1, 1)}
    output = json.dumps(data, default=custom_json_serializer)
    parsed = json.loads(output)
    assert parsed["ts"] == "2024-01-01T00:00:00"
