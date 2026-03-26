"""Extended tests for cli_tool_audit.audit_cache module."""

import datetime
from unittest.mock import patch

import pytest

from cli_tool_audit.audit_cache import AuditFacade, custom_json_deserializer
from cli_tool_audit.models import CliToolConfig, SchemaType, ToolCheckResult


def _make_tool_config(name="mytool") -> CliToolConfig:
    return CliToolConfig(name=name, version="1.0.0", schema=SchemaType.SEMVER)


def _make_check_result(tool="mytool", is_compatible="Compatible", is_available=True) -> ToolCheckResult:
    return ToolCheckResult(
        tool=tool,
        desired_version="1.0.0",
        is_needed_for_os=True,
        is_available=is_available,
        is_snapshot=False,
        found_version="1.0.0",
        parsed_version="1.0.0",
        is_compatible=is_compatible,
        is_broken=False,
        last_modified=None,
        tool_config=_make_tool_config(tool),
    )


# ---------------------------------------------------------------------------
# custom_json_deserializer
# ---------------------------------------------------------------------------


class TestCustomJsonDeserializer:
    def test_converts_last_modified_string(self):
        data = {"last_modified": "2024-01-15T10:30:00"}
        result = custom_json_deserializer(data)
        assert isinstance(result["last_modified"], datetime.datetime)

    def test_ignores_none_last_modified(self):
        data = {"last_modified": None}
        result = custom_json_deserializer(data)
        assert result["last_modified"] is None

    def test_converts_tool_config(self):
        data = {
            "tool_config": {
                "name": "mytool",
                "version": "1.0.0",
                "version_switch": "--version",
                "schema": "semver",
                "if_os": None,
                "tags": None,
                "install_command": None,
                "install_docs": None,
            }
        }
        result = custom_json_deserializer(data)
        assert isinstance(result["tool_config"], CliToolConfig)
        assert result["tool_config"].schema == SchemaType.SEMVER

    def test_passthrough_for_unrelated_data(self):
        data = {"foo": "bar", "count": 42}
        result = custom_json_deserializer(data)
        assert result == {"foo": "bar", "count": 42}


# ---------------------------------------------------------------------------
# AuditFacade
# ---------------------------------------------------------------------------


class TestAuditFacade:
    def test_cache_dir_created(self, tmp_path):
        _facade = AuditFacade(cache_dir=tmp_path / "cache")
        assert (tmp_path / "cache").exists()

    def test_gitignore_created_in_parent(self, tmp_path):
        cache_dir = tmp_path / "subdir" / "cache"
        _facade = AuditFacade(cache_dir=cache_dir)
        gitignore = cache_dir.parent / ".gitignore"
        assert gitignore.exists()

    def test_get_cache_filename_sanitizes_dots(self, tmp_path):
        facade = AuditFacade(cache_dir=tmp_path)
        config = _make_tool_config("my.tool")
        filename = facade.get_cache_filename(config)
        assert "my_tool" in filename.name

    def test_get_cache_filename_includes_hash(self, tmp_path):
        facade = AuditFacade(cache_dir=tmp_path)
        config = _make_tool_config("mytool")
        filename = facade.get_cache_filename(config)
        assert config.cache_hash() in filename.name

    def test_cache_miss_returns_none(self, tmp_path):
        facade = AuditFacade(cache_dir=tmp_path)
        config = _make_tool_config("notcached")
        result = facade.read_from_cache(config)
        assert result is None
        assert facade.cache_hit is False

    def test_write_then_read_cache(self, tmp_path):
        facade = AuditFacade(cache_dir=tmp_path)
        config = _make_tool_config()
        expected = _make_check_result()
        facade.write_to_cache(config, expected)
        result = facade.read_from_cache(config)
        assert result is not None
        assert result.tool == "mytool"
        assert facade.cache_hit is True

    def test_problems_not_cached(self, tmp_path):
        facade = AuditFacade(cache_dir=tmp_path)
        config = _make_tool_config()
        # A problem result (unavailable)
        problem_result = _make_check_result(is_available=False, is_compatible=">=2.0.0 != 1.0.0")

        with patch.object(facade.audit_manager, "call_and_check", return_value=problem_result):
            result = facade.call_and_check(config)

        assert result.is_available is False
        # Should NOT be cached
        assert facade.read_from_cache(config) is None

    def test_good_results_are_cached(self, tmp_path):
        facade = AuditFacade(cache_dir=tmp_path)
        config = _make_tool_config()
        good_result = _make_check_result()

        with patch.object(facade.audit_manager, "call_and_check", return_value=good_result):
            facade.call_and_check(config)

        cached = facade.read_from_cache(config)
        assert cached is not None

    def test_second_call_hits_cache(self, tmp_path):
        facade = AuditFacade(cache_dir=tmp_path)
        config = _make_tool_config()
        good_result = _make_check_result()

        with patch.object(facade.audit_manager, "call_and_check", return_value=good_result) as mock_check:
            facade.call_and_check(config)
            facade.call_and_check(config)

        # audit_manager.call_and_check should only be called once
        mock_check.assert_called_once()

    def test_clear_old_cache_removes_stale_files(self, tmp_path):
        facade = AuditFacade(cache_dir=tmp_path)
        # Create a stale cache file
        stale = tmp_path / "old_cache.json"
        stale.write_text("{}", encoding="utf-8")
        import os

        old_time = datetime.datetime(2020, 1, 1).timestamp()
        os.utime(stale, (old_time, old_time))

        facade.clear_old_cache_files()
        assert not stale.exists()

    def test_corrupt_cache_file_raises_json_decode_error(self, tmp_path):
        # BUG: read_from_cache catches TypeError (for bad keys) but not JSONDecodeError
        # for corrupt/invalid JSON. A corrupt cache file raises instead of returning None.
        import json

        facade = AuditFacade(cache_dir=tmp_path)
        config = _make_tool_config()
        cache_file = facade.get_cache_filename(config)
        cache_file.write_text("not valid json {{{{", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            facade.read_from_cache(config)
