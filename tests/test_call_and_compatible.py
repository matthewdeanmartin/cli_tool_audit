"""Tests for cli_tool_audit.call_and_compatible module."""

import sys
import threading
from unittest.mock import patch

from cli_tool_audit.call_and_compatible import check_tool_wrapper
from cli_tool_audit.models import CliToolConfig, SchemaType, ToolCheckResult


def _make_result(tool="mytool", is_available=True, is_compatible="Compatible") -> ToolCheckResult:
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
        tool_config=CliToolConfig(name=tool, schema=SchemaType.SEMVER),
    )


class TestCheckToolWrapper:
    def test_wrong_os_returns_skipped_result(self):
        wrong_os = "win32" if sys.platform != "win32" else "linux"
        config = CliToolConfig(name="mytool", version="1.0.0", if_os=wrong_os)
        lock = threading.Lock()
        result = check_tool_wrapper(("mytool", config, lock, False))
        assert result.is_needed_for_os is False
        assert result.is_available is False

    def test_correct_os_proceeds(self):
        config = CliToolConfig(name="mytool", version="1.0.0")
        lock = threading.Lock()
        expected = _make_result()
        with patch("cli_tool_audit.call_and_compatible.audit_manager.AuditManager") as MockMgr:
            MockMgr.return_value.call_and_check.return_value = expected
            result = check_tool_wrapper(("mytool", config, lock, False))
        assert result.is_needed_for_os is True

    def test_cache_disabled_uses_audit_manager(self):
        config = CliToolConfig(name="mytool", version="1.0.0")
        lock = threading.Lock()
        expected = _make_result()
        with patch("cli_tool_audit.call_and_compatible.audit_manager.AuditManager") as MockMgr:
            MockMgr.return_value.call_and_check.return_value = expected
            check_tool_wrapper(("mytool", config, lock, False))
        MockMgr.return_value.call_and_check.assert_called_once()

    def test_version_switch_defaults_to_version(self):
        config = CliToolConfig(name="mytool", version="1.0.0", version_switch=None)
        lock = threading.Lock()
        expected = _make_result()
        with patch("cli_tool_audit.call_and_compatible.audit_manager.AuditManager") as MockMgr:
            MockMgr.return_value.call_and_check.return_value = expected
            check_tool_wrapper(("mytool", config, lock, False))
        # After wrapper, config.version_switch should be set to "--version"
        assert config.version_switch == "--version"

    def test_config_name_set_to_tool_arg(self):
        config = CliToolConfig(name="oldname", version="1.0.0")
        lock = threading.Lock()
        expected = _make_result()
        with patch("cli_tool_audit.call_and_compatible.audit_manager.AuditManager") as MockMgr:
            MockMgr.return_value.call_and_check.return_value = expected
            check_tool_wrapper(("newname", config, lock, False))
        assert config.name == "newname"
