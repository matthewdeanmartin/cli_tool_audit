from cli_tool_audit.view_npm_stress_test import report_for_npm_tools
from cli_tool_audit.view_pipx_stress_test import report_for_pipx_tools
from cli_tool_audit.view_venv_stress_test import report_for_venv_tools
from cli_tool_audit.views import report_from_pyproject_toml


def test_report_for_npm_tools():
    report_for_npm_tools(max_count=2)


def test_report_for_pipx_tools():
    report_for_pipx_tools(max_count=2)


def test_report_for_venv_tools():
    report_for_venv_tools(max_count=2)


def test_report_for_pyproject_toml():
    for file_format in ["json", "table", "xml", "json-compact", "csv"]:
        report_from_pyproject_toml(exit_code_on_failure=False, file_format=file_format)
