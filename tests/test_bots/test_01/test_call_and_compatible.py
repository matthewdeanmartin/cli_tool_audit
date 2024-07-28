import sys
import threading
from unittest.mock import MagicMock, patch

import pytest

from cli_tool_audit.call_and_compatible import check_tool_wrapper
from cli_tool_audit.models import CliToolConfig, ToolCheckResult


@pytest.mark.parametrize(
    "tool_info, expected_result",
    [
        # Case where the OS does not match
        (
            ("mock_tool", CliToolConfig(name="name", if_os="wrong_os", version="1.2.3"), threading.Lock(), False),
            ToolCheckResult(
                is_needed_for_os=False,
                tool="mock_tool",
                desired_version="1.2.3",
                is_available=False,
                found_version=None,
                parsed_version=None,
                is_snapshot=False,
                is_compatible=f"{sys.platform}, not wrong_os",
                is_broken=False,
                last_modified=None,
                tool_config=MagicMock(),
            ),
        ),
        # Case where the cache is enabled and a cached response is successful
        (
            ("mock_tool", CliToolConfig(version="1.0.0", name="name"), threading.Lock(), True),
            ToolCheckResult(
                is_needed_for_os=True,
                tool="mock_tool",
                desired_version="1.0.0",
                is_available=True,
                found_version="1.0.0",
                parsed_version="1.0.0",
                is_snapshot=False,
                is_compatible="",
                is_broken=False,
                last_modified=None,
                tool_config=MagicMock(),
            ),
        ),
        # Case where the cache is disabled and a default call is made
        (
            ("mock_tool", CliToolConfig(version="2.0", name="name"), threading.Lock(), False),
            ToolCheckResult(
                is_needed_for_os=True,
                tool="mock_tool",
                desired_version="2.0",
                is_available=True,
                found_version="2.0",
                parsed_version="2.0",
                is_snapshot=False,
                is_compatible="",
                is_broken=False,
                last_modified=None,
                tool_config=MagicMock(),
            ),
        ),
    ],
)
def test_check_tool_wrapper(tool_info, expected_result, mocker):
    # Mock the dependencies
    if tool_info[1].if_os and not sys.platform.startswith(tool_info[1].if_os):
        with patch("cli_tool_audit.models.ToolCheckResult", return_value=expected_result) as _mock_result:
            result = check_tool_wrapper(tool_info)
            assert result == expected_result
    else:
        audit_facade_mock = mocker.patch("cli_tool_audit.audit_cache.AuditFacade")
        audit_manager_mock = mocker.patch("cli_tool_audit.audit_manager.AuditManager")

        # Setup return values for the mocks
        if tool_info[3]:  # If cache is enabled
            audit_facade_instance = audit_facade_mock.return_value
            audit_facade_instance.call_and_check.return_value = expected_result
        else:  # If cache is disabled
            audit_manager_instance = audit_manager_mock.return_value
            audit_manager_instance.call_and_check.return_value = expected_result

        # Call the function
        result = check_tool_wrapper(tool_info)

        # Validate the result against the expected outcome
        assert result == expected_result


@pytest.fixture
def mock_tool_info():
    # Fixture to provide a basic set of tool info for our tests
    return (
        "mock_tool",
        CliToolConfig(version="1.0.0", name="mock_tool"),
        threading.Lock(),
        True,
    )


@pytest.fixture
def mock_audit_facade(mocker):
    audit_facade_mock = mocker.patch("cli_tool_audit.audit_cache.AuditFacade")
    return audit_facade_mock.return_value


@pytest.fixture
def mock_audit_manager(mocker):
    audit_manager_mock = mocker.patch("cli_tool_audit.audit_manager.AuditManager")
    return audit_manager_mock.return_value


def test_check_tool_wrapper_happy_path_with_cache_enabled(mock_tool_info, mock_audit_facade):
    # Simulate a successful tool check cache read
    mock_audit_facade.call_and_check.return_value = ToolCheckResult(
        is_needed_for_os=True,
        tool=mock_tool_info[0],
        desired_version=mock_tool_info[1].version,
        is_available=True,
        found_version="1.0.0",
        parsed_version="1.0.0",
        is_snapshot=False,
        is_compatible="mocked_platform, not some_os",
        is_broken=False,
        last_modified=None,
        tool_config=mock_tool_info[1],
    )

    result = check_tool_wrapper(mock_tool_info)

    assert result.is_available
    assert result.found_version == "1.0.0"


def test_check_tool_wrapper_happy_path_without_cache(mock_tool_info, mock_audit_manager):
    # Simulate a successful tool check without cache
    mock_tool_info = ("mock_tool", CliToolConfig(version="1.0.0", name="mock_tool"), threading.Lock(), False)
    mock_audit_manager.call_and_check.return_value = ToolCheckResult(
        is_needed_for_os=True,
        tool=mock_tool_info[0],
        desired_version=mock_tool_info[1].version,
        is_available=True,
        found_version="1.0.0",
        parsed_version="1.0.0",
        is_snapshot=False,
        is_compatible="mocked_platform, not some_os",
        is_broken=False,
        last_modified=None,
        tool_config=mock_tool_info[1],
    )

    result = check_tool_wrapper(mock_tool_info)

    assert result.is_available
    assert result.found_version == "1.0.0"


def test_check_tool_wrapper_edge_case_no_version(mock_tool_info, mock_audit_facade):
    # Edge case: Simulate a tool config with no version specified
    mock_tool_info = ("mock_tool", CliToolConfig(version=None, name="mock_tool"), threading.Lock(), True)
    mock_audit_facade.call_and_check.return_value = ToolCheckResult(
        is_needed_for_os=True,
        tool=mock_tool_info[0],
        desired_version="0.0.0",
        is_available=False,
        found_version=None,
        parsed_version=None,
        is_snapshot=False,
        is_compatible="mocked_platform, not some_os",
        is_broken=True,
        last_modified=None,
        tool_config=mock_tool_info[1],
    )

    result = check_tool_wrapper(mock_tool_info)

    assert not result.is_available
    assert result.found_version is None
