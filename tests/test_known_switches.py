"""Tests for cli_tool_audit.known_switches module."""

from cli_tool_audit.known_switches import KNOWN_SWITCHES


def test_known_switches_is_dict():
    assert isinstance(KNOWN_SWITCHES, dict)


def test_npm_switch():
    assert KNOWN_SWITCHES["npm"] == "version"


def test_terraform_switch():
    assert KNOWN_SWITCHES["terraform"] == "-version"


def test_java_switch():
    assert KNOWN_SWITCHES["java"] == "-version"


def test_all_values_are_strings():
    for key, value in KNOWN_SWITCHES.items():
        assert isinstance(key, str), f"key {key!r} is not a string"
        assert isinstance(value, str), f"value for {key!r} is not a string"


def test_fallback_for_unknown_tool():
    result = KNOWN_SWITCHES.get("nonexistent_tool_xyz", "--version")
    assert result == "--version"
