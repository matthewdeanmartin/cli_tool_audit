from unittest.mock import patch

from cli_tool_audit.models import CliToolConfig, SchemaType, ToolCheckResult
from cli_tool_audit.views import get_install_hints, report_from_pyproject_toml, summarize_failures


def test_summarize_failures_uses_human_readable_reasons():
    results = [
        ToolCheckResult(
            tool="docker",
            desired_version=">=26.0.0",
            is_needed_for_os=True,
            is_available=False,
            is_snapshot=False,
            found_version=None,
            parsed_version=None,
            is_compatible="Compatible",
            is_broken=False,
            last_modified=None,
            tool_config=CliToolConfig(name="docker", schema=SchemaType.SEMVER),
        ),
        ToolCheckResult(
            tool="mypy",
            desired_version=">=1.10.0",
            is_needed_for_os=True,
            is_available=True,
            is_snapshot=False,
            found_version="1.0.0",
            parsed_version="1.0.0",
            is_compatible=">=1.10.0 != 1.0.0",
            is_broken=False,
            last_modified=None,
            tool_config=CliToolConfig(name="mypy", version=">=1.10.0", schema=SchemaType.SEMVER),
        ),
    ]

    assert (
        summarize_failures(results) == "2 tools failed: docker (not found), mypy (outdated (have 1.0.0, need >=1.10.0))"
    )


def test_get_install_hints_returns_only_configured_hints():
    results = [
        ToolCheckResult(
            tool="mypy",
            desired_version=">=1.10.0",
            is_needed_for_os=True,
            is_available=False,
            is_snapshot=False,
            found_version=None,
            parsed_version=None,
            is_compatible="Compatible",
            is_broken=False,
            last_modified=None,
            tool_config=CliToolConfig(
                name="mypy",
                schema=SchemaType.SEMVER,
                install_command="pipx install mypy",
                install_docs="https://mypy.readthedocs.io/",
            ),
        ),
        ToolCheckResult(
            tool="docker",
            desired_version=">=26.0.0",
            is_needed_for_os=True,
            is_available=False,
            is_snapshot=False,
            found_version=None,
            parsed_version=None,
            is_compatible="Compatible",
            is_broken=False,
            last_modified=None,
            tool_config=CliToolConfig(name="docker", schema=SchemaType.SEMVER),
        ),
    ]

    assert get_install_hints(results) == [
        "mypy: run `pipx install mypy`; see `https://mypy.readthedocs.io/`",
    ]


def test_report_from_pyproject_toml_prints_summary_and_fix_hints(capsys):
    config = CliToolConfig(
        name="mypy",
        schema=SchemaType.SEMVER,
        install_command="pipx install mypy",
        install_docs="https://mypy.readthedocs.io/",
    )
    results = [
        ToolCheckResult(
            tool="mypy",
            desired_version=">=1.10.0",
            is_needed_for_os=True,
            is_available=False,
            is_snapshot=False,
            found_version=None,
            parsed_version=None,
            is_compatible="Compatible",
            is_broken=False,
            last_modified=None,
            tool_config=config,
        )
    ]

    with patch("cli_tool_audit.views.process_tools", return_value=results):
        exit_code = report_from_pyproject_toml(
            file_path=None,
            config_as_dict={"mypy": config},
            exit_code_on_failure=False,
            file_format="table",
            show_fix=True,
        )

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "1 tool failed: mypy (not found)" in captured
    assert "Install hints:" in captured
    assert "- mypy: run `pipx install mypy`; see `https://mypy.readthedocs.io/`" in captured
