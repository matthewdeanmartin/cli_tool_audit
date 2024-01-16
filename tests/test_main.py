from unittest.mock import patch

import pytest

import cli_tool_audit.__main__ as app


@pytest.fixture
def mock_config_manager():
    with patch("cli_tool_audit.config_manager.ConfigManager") as mock:
        yield mock


@pytest.fixture
def mock_freeze_to_screen():
    with patch("cli_tool_audit.freeze.freeze_to_screen") as mock:
        yield mock


@pytest.fixture
def mock_report_from_pyproject_toml():
    with patch("cli_tool_audit.views.report_from_pyproject_toml") as mock:
        yield mock


@pytest.fixture
def mock_report_for_pipx_tools():
    with patch("cli_tool_audit.view_pipx_stress_test.report_for_pipx_tools") as mock:
        yield mock


@pytest.fixture
def mock_report_for_venv_tools():
    with patch("cli_tool_audit.view_venv_stress_test.report_for_venv_tools") as mock:
        yield mock


# Test default behavior
def test_default_behavior(mock_report_from_pyproject_toml):
    argv = []
    app.main(argv)
    mock_report_from_pyproject_toml.assert_called_once()


# Test freeze command
def test_freeze_command(mock_freeze_to_screen):
    argv = ["freeze", "tool1", "tool2"]
    app.main(argv)
    mock_freeze_to_screen.assert_called_once_with(["tool1", "tool2"])


# Test audit command
def test_audit_command(mock_report_from_pyproject_toml):
    argv = ["audit"]
    app.main(argv)
    mock_report_from_pyproject_toml.assert_called_once()


# Test demo command with pipx
def test_demo_command_pipx(mock_report_for_pipx_tools):
    argv = ["--demo", "pipx"]
    app.main(argv)
    mock_report_for_pipx_tools.assert_called_once()


def test_demo_command_venv(mock_report_for_venv_tools):
    argv = ["--demo", "venv"]
    app.main(argv)
    mock_report_for_venv_tools.assert_called_once()
