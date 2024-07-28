import os
import sys
from unittest.mock import MagicMock, patch

import pytest

import cli_tool_audit.models as models
from cli_tool_audit.view_venv_stress_test import get_executables_in_venv


@pytest.mark.parametrize("platform,expected_executables", [
    ("win32", ["tool1.exe", "tool2.exe"]),
    ("win32", ["tool1.exe"]), # Test with one executable
    ("win32", []),            # Test with no executables
    ("linux", ["tool1", "tool2", "tool3"]),
    ("linux", ["tool1"]),     # Test with one executable
    ("linux", []),            # Test with no executables
])
def test_get_executables_in_venv(monkeypatch, platform, expected_executables, tmp_path):
    # Set the mock platform
    monkeypatch.setattr(sys, 'platform', platform)
    
    # Set the executable directory based on the mocked platform
    if platform == "win32":
        os.path.join(tmp_path, "Scripts")
    else:
        os.path.join(tmp_path, "bin")

    # Mock the glob.glob to return specific executables based on test cases
    with patch("glob.glob") as mock_glob:
        mock_glob.return_value = [str(tmp_path / exec_name) for exec_name in expected_executables]

        # Call the function to test
        executables = get_executables_in_venv(str(tmp_path))

        # Check the result
        assert executables == expected_executables

# Helper function to create mock ToolCheckResult
def create_mock_tool_check_result(status="ok", is_problem=False):
    mock_result = MagicMock(spec=models.ToolCheckResult)
    mock_result.status.return_value = status
    mock_result.is_problem.return_value = is_problem
    return mock_result



