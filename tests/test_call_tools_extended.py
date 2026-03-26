"""Extended tests for cli_tool_audit.call_tools module."""

import subprocess
from datetime import datetime
from unittest.mock import patch

from cli_tool_audit.call_tools import check_tool_availability, extract_version_output, get_command_last_modified_date
from cli_tool_audit.models import SchemaType

# ---------------------------------------------------------------------------
# extract_version_output
# ---------------------------------------------------------------------------


class TestExtractVersionOutput:
    def test_prefers_stdout(self):
        result = extract_version_output("1.2.3", "error text")
        assert result == "1.2.3"

    def test_falls_back_to_stderr(self):
        result = extract_version_output(None, "version 1.2.3")
        assert result == "version 1.2.3"

    def test_strips_whitespace(self):
        result = extract_version_output("  1.2.3  \n", None)
        assert result == "1.2.3"

    def test_empty_stdout_uses_stderr(self):
        result = extract_version_output("", "1.2.3")
        assert result == "1.2.3"

    def test_whitespace_only_stdout_uses_stderr(self):
        result = extract_version_output("   \n  ", "1.2.3")
        assert result == "1.2.3"

    def test_both_none_returns_none(self):
        result = extract_version_output(None, None)
        assert result is None

    def test_both_empty_returns_none(self):
        result = extract_version_output("", "")
        assert result is None

    def test_multiline_stdout_kept_intact(self):
        multiline = "tool version 1.2.3\nsome other info"
        result = extract_version_output(multiline, None)
        assert result == multiline.strip()


# ---------------------------------------------------------------------------
# get_command_last_modified_date
# ---------------------------------------------------------------------------


class TestGetCommandLastModifiedDate:
    def test_returns_none_for_nonexistent_tool(self):
        result = get_command_last_modified_date("__tool_that_does_not_exist_xyz__")
        assert result is None

    def test_returns_datetime_for_real_tool(self):
        # python is virtually always available
        import shutil

        if shutil.which("python"):
            result = get_command_last_modified_date("python")
            assert result is not None
            assert isinstance(result, datetime)


# ---------------------------------------------------------------------------
# check_tool_availability
# ---------------------------------------------------------------------------


class TestCheckToolAvailability:
    def test_unavailable_tool_returns_not_available(self):
        result = check_tool_availability("__tool_xyz_does_not_exist__", SchemaType.SEMVER)
        assert result.is_available is False
        assert result.is_broken is True
        assert result.version is None

    @patch("cli_tool_audit.call_tools.get_command_last_modified_date", return_value=datetime(2024, 1, 1))
    @patch("cli_tool_audit.call_tools.subprocess.run")
    def test_successful_invocation(self, mock_run, _mock_modified):
        mock_run.return_value = type("R", (), {"stdout": "1.2.3", "stderr": "", "returncode": 0})()
        result = check_tool_availability("mytool", SchemaType.SEMVER)
        assert result.is_available is True
        assert result.is_broken is False
        assert result.version == "1.2.3"

    @patch("cli_tool_audit.call_tools.get_command_last_modified_date", return_value=datetime(2024, 1, 1))
    @patch("cli_tool_audit.call_tools.subprocess.run")
    def test_nonzero_exit_with_version_output_not_broken(self, mock_run, _mock_modified):
        mock_run.side_effect = subprocess.CalledProcessError(1, ["tool", "--version"], output="tool 3.0.0", stderr="")
        result = check_tool_availability("tool", SchemaType.SEMVER)
        assert result.is_available is True
        assert result.is_broken is False
        assert result.version == "tool 3.0.0"

    @patch("cli_tool_audit.call_tools.get_command_last_modified_date", return_value=datetime(2024, 1, 1))
    @patch("cli_tool_audit.call_tools.subprocess.run")
    def test_nonzero_exit_without_output_is_broken(self, mock_run, _mock_modified):
        mock_run.side_effect = subprocess.CalledProcessError(1, ["tool", "--version"], output="", stderr="")
        result = check_tool_availability("tool", SchemaType.SEMVER)
        assert result.is_available is True
        assert result.is_broken is True
        assert result.version is None

    @patch("cli_tool_audit.call_tools.get_command_last_modified_date", return_value=datetime(2024, 1, 1))
    def test_existence_schema_skips_version_call(self, _mock_modified):
        result = check_tool_availability("anytool", SchemaType.EXISTENCE)
        assert result.is_available is True
        assert result.is_broken is False
        assert result.version is None

    @patch("cli_tool_audit.call_tools.get_command_last_modified_date", return_value=datetime(2024, 1, 1))
    @patch("cli_tool_audit.call_tools.subprocess.run")
    def test_version_on_stderr(self, mock_run, _mock_modified):
        mock_run.return_value = type("R", (), {"stdout": "", "stderr": "version 2.1.0", "returncode": 0})()
        result = check_tool_availability("mytool", SchemaType.SEMVER)
        assert result.version == "version 2.1.0"

    @patch("cli_tool_audit.call_tools.get_command_last_modified_date", return_value=datetime(2024, 1, 1))
    @patch("cli_tool_audit.call_tools.subprocess.run")
    def test_uses_known_switch_for_npm(self, mock_run, _mock_modified):
        mock_run.return_value = type("R", (), {"stdout": "8.0.0", "stderr": "", "returncode": 0})()
        check_tool_availability("npm", SchemaType.SEMVER)
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd == ["npm", "version"]

    @patch("cli_tool_audit.call_tools.get_command_last_modified_date", return_value=datetime(2024, 1, 1))
    @patch("cli_tool_audit.call_tools.subprocess.run")
    def test_custom_version_switch_used(self, mock_run, _mock_modified):
        mock_run.return_value = type("R", (), {"stdout": "1.0", "stderr": "", "returncode": 0})()
        check_tool_availability("mytool", SchemaType.SEMVER, version_switch="-V")
        args, _ = mock_run.call_args
        assert args[0] == ["mytool", "-V"]
