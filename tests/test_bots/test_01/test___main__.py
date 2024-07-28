from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli_tool_audit.__main__ import handle_create, reduce_args_tool_cli_tool_config_args


@pytest.mark.parametrize(
    "input_args, expected_output",
    [
        # Test case 1: All valid fields
        (
            Namespace(tool="example_tool", version="1.0.0", version_switch="latest", schema="semver", if_os="linux"),
            {"version": "1.0.0", "version_switch": "latest", "schema": "semver", "if_os": "linux"},
        ),
        # Test case 2: Mixed fields
        (Namespace(tool="example_tool", version="1.0.0", irrelevant="ignore_this"), {"version": "1.0.0"}),
        # Test case 3: No valid fields
        (Namespace(irrelevant="ignore_this"), {}),
    ],
)
def test_reduce_args_tool_cli_tool_config_args(input_args, expected_output):
    """
    Test reduce_args_tool_cli_tool_config_args function.

    Args:
        input_args: Namespace object simulating command-line arguments.
        expected_output: Expected dictionary after reduction.
    """
    # Invoke the function with mocked arguments
    result = reduce_args_tool_cli_tool_config_args(input_args)

    # Check if the result matches expected output
    assert result == expected_output


@pytest.mark.parametrize(
    "exception, expected_message",
    [
        (ValueError("Tool already exists."), "Tool already exists."),
        (Exception("Unexpected error occurred."), "Unexpected error occurred."),
    ],
)
def test_handle_create_with_exceptions(mocker, exception, expected_message):
    """
    Test the handle_create function for handling exceptions.

    Args:
        mocker: Pytest mock fixture.
        exception: Exception to be raised while creating tool config.
        expected_message: Expected output message.
    """
    # Arrange
    mock_config_manager = MagicMock()
    mock_config_manager.create_tool_config.side_effect = exception

    # Mock the ConfigManager to use the mocked instance
    with patch("cli_tool_audit.__main__.config_manager.ConfigManager", return_value=mock_config_manager):
        # Create an argparse Namespace that simulates command line arguments
        args = Namespace(tool="example_tool", config=str(Path("mock_config.toml")))

        # Act and Assert
        if isinstance(exception, ValueError):
            with pytest.raises(ValueError, match=expected_message):
                handle_create(args)
        else:
            try:
                handle_create(args)
            except Exception as e:
                assert str(e) == expected_message


@pytest.fixture
def mock_config_manager():
    """Fixture to create a mocked ConfigManager."""
    with patch("cli_tool_audit.__main__.config_manager.ConfigManager") as MockConfigManager:
        # Create a mock instance of ConfigManager
        mock_instance = MockConfigManager.return_value
        yield mock_instance


def test_handle_create_success(mock_config_manager):
    """Test the happy path scenario for handle_create."""
    # Arrange
    tool_name = "example_tool"
    config_data = {"version": "1.0.0"}

    # Mock the method to succeed
    mock_config_manager.create_tool_config.return_value = None

    args = Namespace(tool=tool_name, config=str(Path("mock_config.toml")), **config_data)

    # Act
    handle_create(args)

    # Assert
    mock_config_manager.create_tool_config.assert_called_once_with(tool_name, config_data)


@pytest.mark.parametrize("existing_tool, expected_message", [("example_tool", "Tool already exists.")])
def test_handle_create_tool_exists(mock_config_manager, existing_tool, expected_message):
    """Test the edge case where a tool configuration already exists."""
    # Arrange
    mock_config_manager.create_tool_config.side_effect = ValueError(expected_message)

    args = Namespace(tool=existing_tool, config=str(Path("mock_config.toml")), version="1.0.0")

    # Act & Assert
    with pytest.raises(ValueError, match=expected_message):
        handle_create(args)


def test_handle_create_unexpected_error(mock_config_manager):
    """Test the error condition when an unexpected error occurs."""
    # Arrange
    mock_config_manager.create_tool_config.side_effect = Exception("Unexpected error occurred.")

    args = Namespace(tool="another_tool", config=str(Path("mock_config.toml")), version="1.0.0")

    # Act
    with pytest.raises(Exception) as exc_info:
        handle_create(args)

    # Assert
    assert str(exc_info.value) == "Unexpected error occurred."
