import os
import subprocess

import pytest

from cli_tool_audit.view_npm_stress_test import report_for_npm_tools
from cli_tool_audit.view_pipx_stress_test import report_for_pipx_tools
from cli_tool_audit.view_venv_stress_test import report_for_venv_tools
from cli_tool_audit.views import report_from_pyproject_toml


def test_report_for_npm_tools():
    # check if npm is on the path
    if os.name == "nt":
        cmd = "npm.cmd"
    else:
        cmd = "npm"
    try:
        subprocess.run([cmd, "--version"], shell=True, capture_output=True, text=True, check=True)  # nosec
    except subprocess.CalledProcessError:
        # mark test as ignored
        pytest.skip("npm not found on path")

    report_for_npm_tools(max_count=2)


def test_report_for_pipx_tools():
    report_for_pipx_tools(max_count=2)


def test_report_for_venv_tools():
    report_for_venv_tools(max_count=2)


def test_report_for_pyproject_toml():
    for file_format in ["json", "table", "xml", "json-compact", "csv"]:
        report_from_pyproject_toml(exit_code_on_failure=False, file_format=file_format)
