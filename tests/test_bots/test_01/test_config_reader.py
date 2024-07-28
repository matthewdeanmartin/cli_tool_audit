from unittest.mock import MagicMock, patch

import pytest

import cli_tool_audit.models as models
from cli_tool_audit.config_reader import read_config
from cli_tool_audit.models import CliToolConfig


@pytest.mark.parametrize(
    "mock_return_value, expected_output, expected_log_message",
    [
        (False, {}, "Config section not found, expected [tool.cli-tools] with values"),  # Section not found
    ],
)
def test_read_config(mocker, mock_return_value, expected_output, expected_log_message, tmp_path):
    # Arrange
    mock_tools = {"tool1": CliToolConfig(name="name"), "tool2": CliToolConfig(name="name")}
    config_file_path = tmp_path / "pyproject.toml"

    # Mocking ConfigManager and its method
    mock_config_manager = MagicMock()
    mock_config_manager.tools = mock_tools if mock_return_value else {}
    mock_config_manager.read_config.return_value = mock_return_value

    with patch("cli_tool_audit.config_manager.ConfigManager", return_value=mock_config_manager):
        if expected_log_message:
            logger_patch = mocker.patch("cli_tool_audit.config_reader.logger.warning")
        else:
            logger_patch = mocker.patch("cli_tool_audit.config_reader.logger.debug")

        # Act
        result = read_config(config_file_path)

        # Assert
        assert result == expected_output
        if expected_log_message:
            logger_patch.assert_called_once_with(expected_log_message)
        else:
            logger_patch.assert_called_once_with(f"Loading config from {config_file_path}")


# Sample successful data for tools
mock_tools_data = {
    "tool1": models.CliToolConfig(name="tool1"),  # Imagine this is properly initialized
    "tool2": models.CliToolConfig(name="tool2"),  # Another initialized object
}


def test_read_config_happy_path(mocker, tmp_path):
    # Arrange
    config_file_path = tmp_path / "pyproject.toml"
    mock_config_manager = MagicMock()
    mock_config_manager.read_config.return_value = True
    mock_config_manager.tools = mock_tools_data

    with patch("cli_tool_audit.config_manager.ConfigManager", return_value=mock_config_manager):
        # Act
        result = read_config(config_file_path)

        # Assert
        assert result == mock_tools_data
        mock_config_manager.read_config.assert_called_once()


def test_read_config_no_tools(mocker, tmp_path):
    # Arrange
    config_file_path = tmp_path / "pyproject.toml"
    mock_config_manager = MagicMock()
    mock_config_manager.read_config.return_value = True
    mock_config_manager.tools = {}

    with patch("cli_tool_audit.config_manager.ConfigManager", return_value=mock_config_manager):
        with patch("cli_tool_audit.config_reader.logger.warning") as _mock_warning:
            # Act
            result = read_config(config_file_path)

            # Assert
            assert result == {}


def test_read_config_malformed_config(mocker, tmp_path):
    # Arrange
    config_file_path = tmp_path / "pyproject.toml"
    mock_config_manager = MagicMock()
    mock_config_manager.read_config.return_value = False
    mock_config_manager.tools = {}

    with patch("cli_tool_audit.config_manager.ConfigManager", return_value=mock_config_manager):
        with patch("cli_tool_audit.config_reader.logger.warning") as mock_warning:
            # Act
            result = read_config(config_file_path)

            # Assert
            assert result == {}
            mock_warning.assert_called_once_with("Config section not found, expected [tool.cli-tools] with values")
