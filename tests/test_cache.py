import json
from unittest.mock import Mock, patch

import pytest

from cli_tool_audit.audit_cache import AuditFacade, custom_json_deserializer
from cli_tool_audit.models import CliToolConfig, SchemaType, ToolCheckResult


@pytest.fixture
def mock_audit_manager():
    with patch("cli_tool_audit.audit_manager.AuditManager") as mock:
        mock_instance = mock.return_value
        mock_instance.call_and_check = Mock()
        yield mock_instance


def test_audit_facade_caching(tmp_path, mock_audit_manager):
    # Setup a mock tool config and result
    tool_config = CliToolConfig(name="test_tool")
    expected_result = ToolCheckResult(
        tool="test_tool",
        is_needed_for_os=True,
        desired_version="0.0.0",
        is_available=True,
        found_version="1.2.3",
        parsed_version=None,
        is_snapshot=False,
        is_compatible="Compatible",
        is_broken=False,
        last_modified=None,
        tool_config=CliToolConfig(
            name="test_tool",
            schema=SchemaType.SEMVER,
            version="0.0.0",
            version_switch="--version",
            if_os=None,
        ),
    )
    mock_audit_manager.call_and_check.return_value = expected_result

    # Instantiate AuditFacade with the tmp_path as cache directory
    facade = AuditFacade(cache_dir=tmp_path)

    # Call and check - should use the mock and write to cache
    result = facade.call_and_check(tool_config)
    assert result == expected_result

    # Verify that the result is cached
    cache_file = facade.get_cache_filename(tool_config)
    assert cache_file.exists()

    # Read the cached result directly and verify its content
    with open(cache_file, encoding="utf-8") as file:
        # dupe code.
        hit = ToolCheckResult(**json.load(file, object_hook=custom_json_deserializer))
    assert not facade.cache_hit
    assert hit == expected_result

    # Call and check again - should read from cache this time
    result = facade.call_and_check(tool_config)
    assert facade.cache_hit
    assert result == expected_result
    mock_audit_manager.call_and_check.assert_called_once()  # Ensure it was called only once
