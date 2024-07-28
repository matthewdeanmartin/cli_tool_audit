from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from cli_tool_audit.models import CliToolConfig, SchemaType, ToolCheckResult


@pytest.mark.parametrize(
    "result, expected_status, expected_is_problem",
    [
        # Test case: Wrong OS
        (
            ToolCheckResult(
                tool="python",
                desired_version="1.0.0",
                is_needed_for_os=False,
                is_available=True,
                is_snapshot=False,
                found_version="1.0.0",
                parsed_version="1.0.0",
                is_compatible="Compatible",
                is_broken=False,
                last_modified=datetime.now(),
                tool_config=CliToolConfig(name="python"),
            ),
            "Wrong OS",
            False,
        ),
        # Test case: Not available
        (
            ToolCheckResult(
                tool="python",
                desired_version="1.0.0",
                is_needed_for_os=True,
                is_available=False,
                is_snapshot=False,
                found_version=None,
                parsed_version=None,
                is_compatible="Incompatible",
                is_broken=False,
                last_modified=datetime.now(),
                tool_config=CliToolConfig(name="python"),
            ),
            "Not available",
            True,
        ),
        # Test case: Compatible
        (
            ToolCheckResult(
                tool="python",
                desired_version="1.0.0",
                is_needed_for_os=True,
                is_available=True,
                is_snapshot=False,
                found_version="1.0.0",
                parsed_version="1.0.0",
                is_compatible="Compatible",
                is_broken=False,
                last_modified=datetime.now(),
                tool_config=CliToolConfig(name="python"),
            ),
            "Compatible",
            False,
        ),
        # Test case: Incompatible
        (
            ToolCheckResult(
                tool="python",
                desired_version="1.0.0",
                is_needed_for_os=True,
                is_available=True,
                is_snapshot=False,
                found_version="1.0.0",
                parsed_version="1.0.0",
                is_compatible="Incompatible",
                is_broken=False,
                last_modified=datetime.now(),
                tool_config=CliToolConfig(name="python"),
            ),
            "Incompatible",
            True,
        ),
    ],
)
def test_tool_check_result(result, expected_status, expected_is_problem):
    assert result.status() == expected_status
    assert result.is_problem() == expected_is_problem


def test_cache_hash_mock_encoding_error():
    # Create an instance of CliToolConfig for testing
    config = CliToolConfig(name="python")

    # Mock the asdict to return a valid dictionary
    mock_asdict = MagicMock(return_value={"name": "python"})

    with patch("cli_tool_audit.models.asdict", mock_asdict):
        with patch("hashlib.md5") as mock_md5:
            # Suppressing an internal call to the encode method by raising an exception
            mock_md5.return_value.hexdigest.side_effect = Exception("Encoding error")

            with pytest.raises(Exception) as exc_info:
                config.cache_hash()

            assert str(exc_info.value) == "Encoding error"


def test_cli_tool_config_happy_path():
    # Happy path for creating a CliToolConfig instance
    config = CliToolConfig(name="python", version="1.0.0", version_switch="--version", schema=SchemaType.SEMVER)

    # Check if the instance is created with correct attributes
    assert config.name == "python"
    assert config.version == "1.0.0"
    assert config.version_switch == "--version"
    assert config.schema == SchemaType.SEMVER


def test_cli_tool_config_edge_cases():
    # Testing edge cases with optional fields
    config = CliToolConfig(name="python")

    # Edge case: no version set
    assert config.version is None

    # Edge case: multiple tags (valid input)
    tags = ["tag1", "tag2"]
    config.tags = tags
    assert config.tags == tags

    # Edge case: install_command is not set
    assert config.install_command is None


def test_tool_check_result_happy_path():
    # Happy path for creating a ToolCheckResult instance
    config = CliToolConfig(name="python", version="1.0.0")
    result = ToolCheckResult(
        tool="python",
        desired_version="1.0.0",
        is_needed_for_os=True,
        is_available=True,
        is_snapshot=False,
        found_version="1.0.0",
        parsed_version="1.0.0",
        is_compatible="Compatible",
        is_broken=False,
        last_modified=datetime.now(),
        tool_config=config,
    )

    # Perform checks on ToolCheckResult attributes and status
    assert result.tool == "python"
    assert result.is_compatible == "Compatible"
    assert result.status() == "Compatible"


def test_tool_check_result_edge_case_wrong_os():
    config = CliToolConfig(name="python")
    result = ToolCheckResult(
        tool="python",
        desired_version="1.0.0",
        is_needed_for_os=False,  # Simulate a wrong OS
        is_available=True,
        is_snapshot=False,
        found_version="1.0.0",
        parsed_version="1.0.0",
        is_compatible="Compatible",
        is_broken=False,
        last_modified=datetime.now(),
        tool_config=config,
    )
    assert result.status() == "Wrong OS"


def test_tool_check_result_not_available():
    config = CliToolConfig(name="python")
    result = ToolCheckResult(
        tool="python",
        desired_version="1.0.0",
        is_needed_for_os=True,
        is_available=False,  # Simulate tool not being available
        is_snapshot=False,
        found_version=None,
        parsed_version=None,
        is_compatible="Incompatible",
        is_broken=False,
        last_modified=datetime.now(),
        tool_config=config,
    )

    assert result.status() == "Not available"


def test_cli_tool_config_cache_hash_error_conditions():
    config = CliToolConfig(name="python", version="1.0.0")

    # Mock asdict to return a potentially problematic dictionary
    mock_asdict = MagicMock(side_effect=Exception("Simulated asdict exception"))

    with patch("cli_tool_audit.models.asdict", mock_asdict):
        with pytest.raises(Exception) as exc_info:
            config.cache_hash()

        assert str(exc_info.value) == "Simulated asdict exception"

        # Verify that asdict was called once
        mock_asdict.assert_called_once()

    # Test the internal handling of hash generation and encoding error
    with patch("cli_tool_audit.models.asdict", return_value={"name": "python", "version": "1.0.0"}):
        with patch("hashlib.md5") as mock_md5:
            mock_md5.return_value.hexdigest.side_effect = Exception("Mocked hash error")

            with pytest.raises(Exception) as exc_info:
                config.cache_hash()

            assert str(exc_info.value) == "Mocked hash error"

            # Ensure md5 was called with the correct data
            mock_md5.assert_called_once()
