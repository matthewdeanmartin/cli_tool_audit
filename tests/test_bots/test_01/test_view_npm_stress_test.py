from cli_tool_audit.view_npm_stress_test import report_for_npm_tools


def test_report_for_npm_tools_no_executables(mocker):
    # Arrange
    mocker.patch("cli_tool_audit.view_npm_stress_test.list_global_npm_executables", return_value=[])

    # Act
    report_for_npm_tools()

    # Assert - No exceptions should be raised, and nothing should be reported
    # Here you will typically check if any logger calls were made or if other expected behavior is followed
    # ... You can include checks on logger if necessary.
