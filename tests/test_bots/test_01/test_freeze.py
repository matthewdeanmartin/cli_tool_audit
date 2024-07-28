import datetime
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

import pytest

from cli_tool_audit.freeze import freeze_requirements, freeze_to_config
from cli_tool_audit.models import SchemaType, ToolAvailabilityResult

# tests/test_freeze.py


@pytest.mark.parametrize(
    "tool_names, expected_results",
    [
        (
            ["tool1", "tool2"],
            {
                "tool1": ToolAvailabilityResult(
                    is_available=True, version="1.0.0", is_broken=False, last_modified=datetime.datetime.now()
                ),
                "tool2": ToolAvailabilityResult(
                    is_available=False, version=None, is_broken=False, last_modified=datetime.datetime.now()
                ),
            },
        ),
        (
            ["tool3"],
            {
                "tool3": ToolAvailabilityResult(
                    is_available=True, version="2.5.1", is_broken=False, last_modified=datetime.datetime.now()
                )
            },
        ),
        (
            ["tool4", "tool5", "tool6"],
            {
                "tool4": ToolAvailabilityResult(
                    is_available=False, version=None, is_broken=False, last_modified=datetime.datetime.now()
                ),
                "tool5": ToolAvailabilityResult(
                    is_available=False, version=None, is_broken=False, last_modified=datetime.datetime.now()
                ),
                "tool6": ToolAvailabilityResult(
                    is_available=True, version="3.1.4", is_broken=False, last_modified=datetime.datetime.now()
                ),
            },
        ),
    ],
)
def test_freeze_requirements(tool_names, expected_results, mocker):
    # Mock the check_tool_availability method
    mock_check_tool_availability = mocker.patch("cli_tool_audit.call_tools.check_tool_availability")

    # Prepare the side effects based on input tool names
    mock_check_tool_availability.side_effect = lambda tool_name, schema, version_switch: expected_results[tool_name]

    # Create a dummy schema (mock object)
    schema = mock.Mock(spec=SchemaType)

    # Call the function under test
    results = freeze_requirements(tool_names, schema)

    # Assertions: Check if results match expected_outputs
    for tool_name in tool_names:
        assert results[tool_name] == expected_results[tool_name]


# tests/test_freeze.py


def test_freeze_to_config_handles_exceptions(mocker):
    # Mocking the ToolAvailabilityResult for the test
    tool_results = {
        "tool1": ToolAvailabilityResult(
            is_available=True, version="1.0.0", is_broken=False, last_modified=datetime.datetime.now()
        ),
        "tool2": ToolAvailabilityResult(
            is_available=True, version="2.0.0", is_broken=False, last_modified=datetime.datetime.now()
        ),
    }

    # Mock the freeze_requirements method to return pre-defined results
    mocker.patch("cli_tool_audit.freeze.freeze_requirements", return_value=tool_results)

    # Create a mock for ConfigManager
    mock_config_manager = mocker.patch("cli_tool_audit.config_manager.ConfigManager")

    # Set up the instance of ConfigManager
    mock_instance = mock_config_manager.return_value

    # Mock read_config method
    mock_instance.read_config.return_value = True

    # Scenario 1: Create or update tool config raises ValueError
    mock_instance.create_update_tool_config.side_effect = ValueError("Config already exists")

    # Path for the config file
    config_path = Path("mock_config.toml")

    # Call freeze_to_config function and check exception handling
    with pytest.raises(ValueError, match="Config already exists"):
        freeze_to_config(["tool1", "tool2"], config_path, mock.Mock())

    # Ensure create_update_tool_config was called with correct parameters
    mock_instance.create_update_tool_config.assert_called_with("tool1", {"version": "1.0.0"})

    # Scenario 2: read_config raises an exception
    mock_instance.read_config.side_effect = Exception("Failed to read config")

    with pytest.raises(Exception, match="Failed to read config"):
        freeze_to_config(["tool1"], config_path, mock.Mock())


# tests/test_freeze.py


def test_freeze_to_config_happy_path(mocker):
    # Define mock return values
    tool_results = {
        "tool1": ToolAvailabilityResult(
            is_available=True, version="1.0.0", is_broken=False, last_modified=datetime.datetime.now()
        ),
        "tool2": ToolAvailabilityResult(
            is_available=True, version="2.0.0", is_broken=False, last_modified=datetime.datetime.now()
        ),
    }

    # Mock freeze_requirements function to return predefined tool results
    mocker.patch("cli_tool_audit.freeze.freeze_requirements", return_value=tool_results)

    # Mock ConfigManager to control its behaviors
    mock_config_manager = mocker.patch("cli_tool_audit.config_manager.ConfigManager")
    mock_instance = mock_config_manager.return_value
    mock_instance.read_config.return_value = True

    # Path for the config file
    config_path = Path("mock_config.toml")

    # Call the function
    freeze_to_config(["tool1", "tool2"], config_path, Mock())

    # Ensure that create_update_tool_config was called for each tool with the correct versions
    mock_instance.create_update_tool_config.assert_any_call("tool1", {"version": "1.0.0"})
    mock_instance.create_update_tool_config.assert_any_call("tool2", {"version": "2.0.0"})
    assert mock_instance.create_update_tool_config.call_count == 2


def test_freeze_to_config_empty_tool_list(mocker):
    # Mock ConfigManager
    mock_config_manager = mocker.patch("cli_tool_audit.config_manager.ConfigManager")
    mock_instance = mock_config_manager.return_value
    mock_instance.read_config.return_value = True

    # Path for the config file
    config_path = Path("mock_config.toml")

    # Call the function with an empty tool list
    freeze_to_config([], config_path, Mock())

    # Ensure that read_config was called once and no update configurations were attempted
    mock_instance.read_config.assert_called_once()
    mock_instance.create_update_tool_config.assert_not_called()


def test_freeze_to_config_all_tools_unavailable(mocker):
    # Define mock return values with all tools unavailable
    tool_results = {
        "tool1": ToolAvailabilityResult(
            is_available=False, version=None, is_broken=False, last_modified=datetime.datetime.now()
        ),
        "tool2": ToolAvailabilityResult(
            is_available=False, version=None, is_broken=False, last_modified=datetime.datetime.now()
        ),
    }

    # Mock freeze_requirements to return unavailable tools
    mocker.patch("cli_tool_audit.freeze.freeze_requirements", return_value=tool_results)

    # Mock ConfigManager
    mock_config_manager = mocker.patch("cli_tool_audit.config_manager.ConfigManager")
    mock_instance = mock_config_manager.return_value
    mock_instance.read_config.return_value = True

    # Path for the config file
    config_path = Path("mock_config.toml")

    # Call the function
    freeze_to_config(["tool1", "tool2"], config_path, Mock())

    # Ensure that create_update_tool_config was not called since all tools are unavailable
    mock_instance.create_update_tool_config.assert_not_called()


def test_freeze_to_config_read_config_error(mocker):
    # Define mock return values
    tool_results = {
        "tool1": ToolAvailabilityResult(
            is_available=True, version="1.0.0", is_broken=False, last_modified=datetime.datetime.now()
        ),
    }

    # Mock freeze_requirements function to return predefined tool results
    mocker.patch("cli_tool_audit.freeze.freeze_requirements", return_value=tool_results)

    # Mock ConfigManager and simulate a read config failure
    mock_config_manager = mocker.patch("cli_tool_audit.config_manager.ConfigManager")
    mock_instance = mock_config_manager.return_value
    mock_instance.read_config.side_effect = Exception("Failed to read config")

    # Path for the config file
    config_path = Path("mock_config.toml")

    # Expect an exception to be raised when trying to read config
    with pytest.raises(Exception, match="Failed to read config"):
        freeze_to_config(["tool1"], config_path, Mock())

    # Ensure no tool config update calls were made
    mock_instance.create_update_tool_config.assert_not_called()


def test_freeze_to_config_creating_update_tool_config_error(mocker):
    # Define mock return values
    tool_results = {
        "tool1": ToolAvailabilityResult(
            is_available=True, version="1.0.0", is_broken=False, last_modified=datetime.datetime.now()
        ),
    }

    # Mock freeze_requirements to return available tool results
    mocker.patch("cli_tool_audit.freeze.freeze_requirements", return_value=tool_results)

    # Mock ConfigManager
    mock_config_manager = mocker.patch("cli_tool_audit.config_manager.ConfigManager")
    mock_instance = mock_config_manager.return_value
    mock_instance.read_config.return_value = True

    # Simulate an error when creating/updating tool config
    mock_instance.create_update_tool_config.side_effect = ValueError("Tool config already exists")

    # Path for the config file
    config_path = Path("mock_config.toml")

    # Expect an exception to be raised when trying to create/update the tool config
    with pytest.raises(ValueError, match="Tool config already exists"):
        freeze_to_config(["tool1"], config_path, Mock())

    # Assert that the tool config was attempted to be created/updated
    mock_instance.create_update_tool_config.assert_called_once_with("tool1", {"version": "1.0.0"})
