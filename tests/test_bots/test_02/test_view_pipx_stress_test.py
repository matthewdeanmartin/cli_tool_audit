from cli_tool_audit.view_pipx_stress_test import extract_apps


# Test extraction of apps from pipx_data
def test_extract_apps():
    pipx_data = {
        "venvs": {"test_venv": {"metadata": {"main_package": {"package_version": "1.0", "apps": ["test_app"]}}}}
    }
    apps_dict = extract_apps(pipx_data)

    assert apps_dict == {"test_app": "1.0"}


# These unit tests will cover the successful and error cases of the
# `report_for_pipx_tools` function as well as the extraction of apps from the pipx
# data.
#
# No more unit tests.
