import subprocess
from datetime import datetime
from unittest.mock import patch

from cli_tool_audit.audit_manager import AuditManager
from cli_tool_audit.call_tools import check_tool_availability
from cli_tool_audit.models import SchemaType


@patch("cli_tool_audit.call_tools.get_command_last_modified_date", return_value=datetime(2024, 1, 1))
@patch("cli_tool_audit.call_tools.subprocess.run")
def test_check_tool_availability_uses_version_output_from_called_process_error(mock_run, _mock_modified):
    mock_run.side_effect = subprocess.CalledProcessError(
        1,
        ["demo", "--version"],
        output="demo 1.2.3",
        stderr="",
    )

    result = check_tool_availability("demo", SchemaType.SEMVER)

    assert result.is_available is True
    assert result.is_broken is False
    assert result.version == "demo 1.2.3"


@patch.object(AuditManager, "get_command_last_modified_date", return_value=datetime(2024, 1, 1))
@patch("cli_tool_audit.audit_manager.subprocess.run")
def test_audit_manager_uses_version_output_from_called_process_error(mock_run, _mock_modified):
    mock_run.side_effect = subprocess.CalledProcessError(
        1,
        ["demo", "--version"],
        output="demo 2.0.0",
        stderr="",
    )

    result = AuditManager().call_tool("demo", SchemaType.SEMVER)

    assert result.is_available is True
    assert result.is_broken is False
    assert result.version == "demo 2.0.0"
