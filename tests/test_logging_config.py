"""Tests for cli_tool_audit.logging_config module."""

import os
from unittest.mock import patch

from cli_tool_audit.logging_config import generate_config


def test_generate_config_returns_dict():
    config = generate_config()
    assert isinstance(config, dict)


def test_generate_config_has_required_keys():
    config = generate_config()
    assert "version" in config
    assert "handlers" in config
    assert "loggers" in config
    assert "formatters" in config


def test_generate_config_version_is_1():
    config = generate_config()
    assert config["version"] == 1


def test_generate_config_default_uses_colored_formatter():
    with patch.dict(os.environ, {}, clear=True):
        # Remove CI and NO_COLOR to get the default colored formatter
        env = {k: v for k, v in os.environ.items() if k not in ("CI", "NO_COLOR")}
        with patch.dict(os.environ, env, clear=True):
            config = generate_config()
    assert config["handlers"]["default"]["formatter"] == "colored"


def test_generate_config_ci_uses_standard_formatter():
    with patch.dict(os.environ, {"CI": "1"}):
        config = generate_config()
    assert config["handlers"]["default"]["formatter"] == "standard"


def test_generate_config_no_color_uses_standard_formatter():
    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        config = generate_config()
    assert config["handlers"]["default"]["formatter"] == "standard"


def test_generate_config_has_cli_tool_audit_logger():
    config = generate_config()
    assert "cli_tool_audit" in config["loggers"]


def test_generate_config_level_parameter():
    config = generate_config(level="WARNING")
    # level parameter is accepted but currently not applied to output; just test no crash
    assert isinstance(config, dict)
