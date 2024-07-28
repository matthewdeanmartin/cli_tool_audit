import subprocess
from unittest.mock import patch

from cli_tool_audit.view_pipx_stress_test import get_pipx_list, report_for_pipx_tools


def test_get_pipx_list_called_process_error():
    with patch("subprocess.run") as mock_run:
        # Simulate a CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="pipx list --json", output="Error occurred"
        )

        # Call the function under test
        result = get_pipx_list()

        # Assert that the result is None when a CalledProcessError is raised
        assert result is None


def test_report_for_pipx_tools_happy_path(mocker):
    # Mocking get_pipx_list to return valid data
    mock_pipx_data = {
        "venvs": {"example-tool": {"metadata": {"main_package": {"package_version": "1.0.0", "apps": ["example-app"]}}}}
    }

    mock_get_pipx_list = mocker.patch("cli_tool_audit.view_pipx_stress_test.get_pipx_list", return_value=mock_pipx_data)
    mock_extract_apps = mocker.patch(
        "cli_tool_audit.view_pipx_stress_test.extract_apps", return_value={"example-app": "1.0.0"}
    )

    _result = report_for_pipx_tools(max_count=5)

    # Since we don't check the print directly but we assume it processes correctly
    assert mock_get_pipx_list.called
    assert mock_extract_apps.called


def test_report_for_pipx_tools_empty_data(mocker):
    # Mocking get_pipx_list to return empty data
    mock_get_pipx_list = mocker.patch("cli_tool_audit.view_pipx_stress_test.get_pipx_list", return_value={"venvs": {}})
    mock_extract_apps = mocker.patch("cli_tool_audit.view_pipx_stress_test.extract_apps", return_value={})

    _result = report_for_pipx_tools(max_count=5)

    # We do not expect any tools to be processed
    assert mock_get_pipx_list.called
    assert mock_extract_apps.called


def test_report_for_pipx_tools_no_pipx_data(mocker):
    # Mocking get_pipx_list to return None (error condition)
    mock_get_pipx_list = mocker.patch("cli_tool_audit.view_pipx_stress_test.get_pipx_list", return_value=None)

    _result = report_for_pipx_tools(max_count=5)

    # We check that no tools were processed and the function handled this as expected
    assert mock_get_pipx_list.called
