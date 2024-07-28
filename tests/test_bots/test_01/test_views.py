from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import cli_tool_audit.models as models
import cli_tool_audit.views as views


@pytest.mark.parametrize(
    "file_path, no_cache, tags, expected_length",
    [
        (Path("test2.toml"), True, ["tag1"], 1),  # Only one tool matches "tag1" in test2.toml
    ],
)
def test_validate(file_path, no_cache, tags, expected_length, mocker):
    # Mock the read_config method to return predefined configurations
    dummy_results = {
        "tool1": MagicMock(spec=models.CliToolConfig, tags=["tag1"]),
        "tool2": MagicMock(spec=models.CliToolConfig, tags=["tag2"]),
        "tool3": MagicMock(spec=models.CliToolConfig, tags=["tag3"]),
        "tool4": MagicMock(spec=models.CliToolConfig, tags=None),
    }

    with patch("cli_tool_audit.config_reader.read_config", return_value=dummy_results):
        mock_tool_result = MagicMock(spec=models.ToolCheckResult)
        mock_tool_result.is_problem.return_value = False

        with patch("cli_tool_audit.call_and_compatible.check_tool_wrapper", return_value=mock_tool_result):
            results = views.validate(file_path=file_path, no_cache=no_cache, tags=tags)

    # Ensure the results length is as expected
    assert len(results) == expected_length


def test_validate_file_not_found(mocker):
    file_path = Path("non_existent.toml")

    # Mocking read_config to raise a FileNotFoundError
    with patch("cli_tool_audit.config_reader.read_config", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            views.validate(file_path=file_path)


def test_validate_happy_path(mocker):
    file_path = Path("pyproject.toml")

    # Mocking a valid configuration with two tools
    valid_config = {
        "tool1": MagicMock(spec=models.CliToolConfig),
        "tool2": MagicMock(spec=models.CliToolConfig),
    }

    # Setting up the return values for the mocked objects
    mock_tool_check_result = MagicMock(spec=models.ToolCheckResult)
    mock_tool_check_result.is_problem.return_value = False

    # Mocking read_config to return a valid configuration
    with patch("cli_tool_audit.config_reader.read_config", return_value=valid_config):
        # Mocking check_tool_wrapper to return mock results
        with patch("cli_tool_audit.call_and_compatible.check_tool_wrapper", return_value=mock_tool_check_result):
            results = views.validate(file_path=file_path)
            assert len(results) == 2  # Two tools in the valid config
            assert all(not result.is_problem() for result in results)  # No problems with tools


def test_validate_edge_case_empty_tools(mocker):
    file_path = Path("pyproject.toml")

    # Mocking an empty configuration
    empty_config = {}

    # Mocking read_config to return an empty configuration
    with patch("cli_tool_audit.config_reader.read_config", return_value=empty_config):
        results = views.validate(file_path=file_path)
        assert len(results) == 0  # No tools to validate


def test_validate_error_conditions_file_not_found(mocker):
    file_path = Path("non_existent.toml")

    # Mocking read_config to raise a FileNotFoundError
    with patch("cli_tool_audit.config_reader.read_config", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            views.validate(file_path=file_path)


def test_validate_no_tags(mocker):
    file_path = Path("pyproject.toml")

    # Mocking a configuration with tools having tags
    valid_config = {
        "tool1": MagicMock(spec=models.CliToolConfig),
        "tool2": MagicMock(spec=models.CliToolConfig),
    }

    # Mocking read_config to return the valid configuration
    with patch("cli_tool_audit.config_reader.read_config", return_value=valid_config):
        # Mocking check_tool_wrapper to return mock results with no problems
        mock_tool_check_result = MagicMock(spec=models.ToolCheckResult)
        mock_tool_check_result.is_problem.return_value = False

        with patch("cli_tool_audit.call_and_compatible.check_tool_wrapper", return_value=mock_tool_check_result):
            results = views.validate(file_path=file_path, tags=None)
            assert len(results) == 2  # Two tools in the valid config
            assert all(not result.is_problem() for result in results)  # No problems with tools


# Note: Additional tests could also be written for specific attributes of ToolCheckResult or other edge cases.
