from cli_tool_audit.view_pipx_stress_test import report_for_pipx_tools
from cli_tool_audit.view_venv_stress_test import report_for_venv_tools
from cli_tool_audit.views import report_from_pyproject_toml


def test_report_for_pipx_tools():
    report_for_pipx_tools()


def test_report_for_venv_tools():
    report_for_venv_tools()


def test_report_for_pyproject_toml():
    report_from_pyproject_toml(exit_code_on_failure=False)
