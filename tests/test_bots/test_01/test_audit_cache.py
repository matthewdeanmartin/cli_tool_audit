import json
from unittest.mock import MagicMock, patch

import pytest

from cli_tool_audit.audit_cache import AuditFacade
from cli_tool_audit.json_utils import custom_json_serializer
from cli_tool_audit.models import CliToolConfig, ToolCheckResult


@pytest.fixture
def fake_tool_config():
    # Create a mock CliToolConfig instance
    config = MagicMock(spec=CliToolConfig)
    config.name = "test_tool"
    config.cache_hash.return_value = "dummy_hash"
    return config


@pytest.fixture
def audit_facade(tmp_path):
    return AuditFacade(cache_dir=tmp_path)


@pytest.mark.parametrize(
    "cache_content, expected_result, expected_hit", [(None, None, False)]  # Test for non-existent file
)
def test_read_from_cache(audit_facade, fake_tool_config, cache_content, expected_result, expected_hit, mocker):
    cache_file = audit_facade.get_cache_filename(fake_tool_config)

    # Write the cache content to the cache file if it's valid JSON
    if cache_content is not None:
        if isinstance(cache_content, dict):
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_content, f, default=custom_json_serializer)  # Write valid JSON
        else:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(cache_content)  # Write invalid JSON

    if expected_hit:
        # Mock the ToolCheckResult to return expected attributes
        mock_result = MagicMock(spec=ToolCheckResult)
        mock_result.is_problem.return_value = False
        mock_result.__dict__.update(cache_content)  # Simulate deserialized result

        mocker.patch("cli_tool_audit.models.ToolCheckResult", return_value=mock_result)

    # Act
    result = audit_facade.read_from_cache(fake_tool_config)

    # Assert
    if expected_result:
        assert result is not None  # Expecting a valid ToolCheckResult
        assert isinstance(result, ToolCheckResult)
        assert audit_facade.cache_hit is True
    else:
        assert result is None
        assert audit_facade.cache_hit is False


# @pytest.fixture
# def fake_tool_config():
#     # Create a mock CliToolConfig instance
#     config = MagicMock(spec=CliToolConfig)
#     config.name = "test_tool"
#     config.cache_hash.return_value = "dummy_hash"
#     return config
#
#
# @pytest.fixture
# def audit_facade(tmp_path):
#     return AuditFacade(cache_dir=tmp_path)


def test_read_from_cache_file_not_found(audit_facade, fake_tool_config):
    # Simulate file not found scenario
    with patch("pathlib.Path.exists", return_value=False):
        result = audit_facade.read_from_cache(fake_tool_config)

    assert result is None
    assert audit_facade.cache_hit is False


# @pytest.fixture
# def fake_tool_config():
#     config = MagicMock(spec=CliToolConfig)
#     config.name = "test_tool"
#     config.cache_hash.return_value = "dummy_hash"
#     return config
#
#
# @pytest.fixture
# def audit_facade(tmp_path):
#     return AuditFacade(cache_dir=tmp_path)


def test_happy_path_write_to_cache(audit_facade, fake_tool_config):
    # Create a mock result to write to the cache
    mock_result = MagicMock(spec=ToolCheckResult)
    mock_result.__dict__ = {"status": "success"}

    # Write to cache
    audit_facade.write_to_cache(fake_tool_config, mock_result)

    # Check that the cache file was created
    cache_filename = audit_facade.get_cache_filename(fake_tool_config)
    assert cache_filename.exists()

    # Verify the content of the cache file
    with open(cache_filename, encoding="utf-8") as f:
        cached_data = json.load(f)
        assert cached_data["status"] == "success"


def test_edge_case_tool_name_with_special_character(audit_facade):
    special_config = MagicMock(spec=CliToolConfig)
    special_config.name = "tool@#"
    special_config.cache_hash.return_value = "special_hash"

    # Write to cache with special character
    cache_filename = audit_facade.get_cache_filename(special_config)
    mock_result = MagicMock(spec=ToolCheckResult)
    mock_result.__dict__ = {"status": "success"}
    audit_facade.write_to_cache(special_config, mock_result)

    assert cache_filename.exists()  # Verify the file was created


def test_edge_case_multiple_cache_writes(audit_facade, fake_tool_config):
    # Write to cache multiple times
    for i in range(3):
        mock_result = MagicMock(spec=ToolCheckResult)
        mock_result.__dict__ = {"status": f"success-{i}"}
        audit_facade.write_to_cache(fake_tool_config, mock_result)

    # Verify the last write has overwritten previous ones
    with open(audit_facade.get_cache_filename(fake_tool_config), encoding="utf-8") as f:
        cached_data = json.load(f)
        assert cached_data["status"] == "success-2"  # Last write in the loop
