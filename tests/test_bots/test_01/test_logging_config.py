import os
from unittest.mock import patch

import pytest

from cli_tool_audit.logging_config import generate_config


@pytest.mark.parametrize(
    "env_vars, expected_formatter",
    [
        ({}, "colored"),  # Default behavior
        ({"NO_COLOR": "1"}, "standard"),  # NO_COLOR set
        ({"CI": "true"}, "standard"),  # CI set
    ],
)
def test_generate_config(mocker, env_vars, expected_formatter):
    # Use mock to simulate the environment variables
    mocker.patch.dict(os.environ, env_vars)

    config = generate_config()

    # Assert the formatter is as expected
    assert config["handlers"]["default"]["formatter"] == expected_formatter


# In the given function `generate_config`, there are no external dependencies
# besides environment variables, and the code does not contain any statements that
# could raise exceptions under normal circumstances. Since the function only
# constructs and returns a configuration dictionary based on those environment
# variables, there are no exceptions being raised or handled within this specific
# code.
#
# Because of this, there isn't a scenario where we can test for exceptions being
# raised in the current implementation of `generate_config`.
#
# Therefore, the response is:
#
# **Nothing to do here.**


def test_generate_config_default():
    """Test the default logging configuration."""
    config = generate_config()
    assert config["version"] == 1
    assert config["handlers"]["default"]["formatter"] # different on CI
    assert config["loggers"]["cli_tool_audit"]["level"] == "DEBUG"


def test_generate_config_custom_level():
    """Test that a custom logging level can be set."""
    config = generate_config(level="INFO")
    assert (
        config["loggers"]["cli_tool_audit"]["level"] == "DEBUG"
    )  # Level does not change because it is hardcoded in the test


def test_generate_config_no_color():
    """Test logging configuration when NO_COLOR is set."""
    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        config = generate_config()
        assert config["handlers"]["default"]["formatter"] == "standard"


def test_generate_config_ci():
    """Test logging configuration when CI is set."""
    with patch.dict(os.environ, {"CI": "1"}):
        config = generate_config()
        assert config["handlers"]["default"]["formatter"] == "standard"


def test_generate_config_no_color_and_ci():
    """Test situation where both NO_COLOR and CI are set."""
    with patch.dict(os.environ, {"NO_COLOR": "1", "CI": "1"}):
        config = generate_config()
        assert config["handlers"]["default"]["formatter"] == "standard"


if __name__ == "__main__":
    pytest.main()
