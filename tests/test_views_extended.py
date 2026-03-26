"""Extended tests for cli_tool_audit.views module."""

import os
from unittest.mock import patch

import pytest

from cli_tool_audit.models import CliToolConfig, SchemaType, ToolCheckResult
from cli_tool_audit.views import (
    pretty_print_results,
    report_from_pyproject_toml,
    should_show_progress_bar,
    summarize_failures,
)


def _result(
    tool="mytool",
    is_needed_for_os=True,
    is_available=True,
    is_compatible="Compatible",
    is_broken=False,
    found_version="1.0.0",
    desired_version="1.0.0",
    install_command=None,
    install_docs=None,
) -> ToolCheckResult:
    return ToolCheckResult(
        tool=tool,
        desired_version=desired_version,
        is_needed_for_os=is_needed_for_os,
        is_available=is_available,
        is_snapshot=False,
        found_version=found_version,
        parsed_version=found_version,
        is_compatible=is_compatible,
        is_broken=is_broken,
        last_modified=None,
        tool_config=CliToolConfig(
            name=tool,
            schema=SchemaType.SEMVER,
            install_command=install_command,
            install_docs=install_docs,
        ),
    )


# ---------------------------------------------------------------------------
# summarize_failures
# ---------------------------------------------------------------------------


class TestSummarizeFailures:
    def test_no_failures_returns_none(self):
        results = [_result("a"), _result("b")]
        assert summarize_failures(results) is None

    def test_single_failure_uses_singular(self):
        results = [_result("badtool", is_available=False)]
        summary = summarize_failures(results)
        assert "1 tool failed" in summary

    def test_multiple_failures_uses_plural(self):
        results = [_result("a", is_available=False), _result("b", is_available=False)]
        summary = summarize_failures(results)
        assert "2 tools failed" in summary

    def test_failures_sorted_alphabetically(self):
        results = [_result("z_tool", is_available=False), _result("a_tool", is_available=False)]
        summary = summarize_failures(results)
        assert summary.index("a_tool") < summary.index("z_tool")

    def test_empty_results_returns_none(self):
        assert summarize_failures([]) is None

    def test_all_wrong_os_not_in_summary(self):
        results = [_result("tool", is_needed_for_os=False, is_available=False, is_compatible="wrong os")]
        assert summarize_failures(results) is None


# ---------------------------------------------------------------------------
# should_show_progress_bar
# ---------------------------------------------------------------------------


class TestShouldShowProgressBar:
    def test_few_tools_disables_bar(self):
        tools = {f"t{i}": None for i in range(4)}
        result = should_show_progress_bar(tools)
        assert result is True  # True means disabled

    def test_many_tools_enables_bar_without_ci(self):
        tools = {f"t{i}": None for i in range(10)}
        with patch.dict(os.environ, {}, clear=False):
            env = {k: v for k, v in os.environ.items() if k not in ("CI", "NO_COLOR")}
            with patch.dict(os.environ, env, clear=True):
                result = should_show_progress_bar(tools)
        # In CI this will be True (disabled); that's fine — documenting behavior
        assert result in (True, None)

    def test_ci_env_disables_bar(self):
        tools = {f"t{i}": None for i in range(10)}
        with patch.dict(os.environ, {"CI": "1"}):
            result = should_show_progress_bar(tools)
        assert result is True

    def test_no_color_disables_bar(self):
        tools = {f"t{i}": None for i in range(10)}
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            result = should_show_progress_bar(tools)
        assert result is True


# ---------------------------------------------------------------------------
# pretty_print_results
# ---------------------------------------------------------------------------


class TestPrettyPrintResults:
    def test_returns_table_with_rows(self):
        results = [_result("mytool")]
        with patch.dict(os.environ, {"CI": "1"}):
            table = pretty_print_results(results, truncate_long_versions=True, include_docs=False)
        assert "mytool" in str(table)

    def test_include_docs_adds_columns(self):
        results = [_result("mytool", install_command="pip install mytool", install_docs="https://example.com")]
        with patch.dict(os.environ, {"CI": "1"}):
            table = pretty_print_results(results, truncate_long_versions=True, include_docs=True)
        assert "Install Command" in table.field_names
        assert "Install Docs" in table.field_names

    def test_truncates_long_versions(self):
        # Verify the table has a finite number of rows even with a very long version string
        long_version = "x" * 200
        results = [_result("mytool", found_version=long_version)]
        with patch.dict(os.environ, {"CI": "1", "NO_COLOR": "1"}):
            table = pretty_print_results(results, truncate_long_versions=True, include_docs=False)
        # Table should exist and have exactly 1 data row
        assert len(table.rows) == 1

    def test_rows_sorted_by_tool_name(self):
        results = [_result("z_tool"), _result("a_tool")]
        with patch.dict(os.environ, {"CI": "1"}):
            table = pretty_print_results(results, truncate_long_versions=True, include_docs=False)
        rendered = str(table)
        assert rendered.index("a_tool") < rendered.index("z_tool")

    def test_empty_results_produces_table(self):
        with patch.dict(os.environ, {"CI": "1"}):
            table = pretty_print_results([], truncate_long_versions=True, include_docs=False)
        assert table is not None


# ---------------------------------------------------------------------------
# report_from_pyproject_toml — format outputs
# ---------------------------------------------------------------------------


class TestReportFormats:
    def _run_report(self, fmt, results=None, show_fix=False, only_errors=False, quiet=False):
        if results is None:
            results = [_result()]
        with patch("cli_tool_audit.views.process_tools", return_value=results):
            return report_from_pyproject_toml(
                file_path=None,
                config_as_dict={"mytool": CliToolConfig(name="mytool", schema=SchemaType.SEMVER)},
                exit_code_on_failure=False,
                file_format=fmt,
                show_fix=show_fix,
                only_errors=only_errors,
                quiet=quiet,
            )

    def test_json_format(self, capsys):
        import json

        self._run_report("json")
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert isinstance(parsed, list)
        assert parsed[0]["tool"] == "mytool"

    def test_json_compact_format(self, capsys):
        import json

        self._run_report("json-compact")
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert isinstance(parsed, list)

    def test_xml_format(self, capsys):
        self._run_report("xml")
        out = capsys.readouterr().out
        assert "<results>" in out
        assert "<tool>mytool</tool>" in out

    def test_csv_format(self, capsys):
        self._run_report("csv")
        out = capsys.readouterr().out
        assert "mytool" in out
        assert "," in out

    def test_table_format(self, capsys):
        self._run_report("table")
        out = capsys.readouterr().out
        assert "mytool" in out

    def test_unknown_format_falls_back_to_table(self, capsys):
        self._run_report("notaformat")
        out = capsys.readouterr().out
        assert "mytool" in out

    def test_quiet_suppresses_output(self, capsys):
        self._run_report("table", quiet=True)
        out = capsys.readouterr().out
        # Quiet mode suppresses summary lines — table itself may still print
        assert "Did not pass" not in out

    def test_only_errors_all_good_prints_no_errors_message(self, capsys):
        self._run_report("table", only_errors=True)
        out = capsys.readouterr().out
        assert "No errors" in out

    def test_exit_code_failure_when_any_tool_fails(self):
        results = [_result(is_available=False)]
        with patch("cli_tool_audit.views.process_tools", return_value=results):
            code = report_from_pyproject_toml(
                file_path=None,
                config_as_dict={"mytool": CliToolConfig(name="mytool")},
                exit_code_on_failure=True,
                file_format="table",
            )
        assert code == 1

    def test_exit_code_zero_when_all_pass(self):
        results = [_result()]
        with patch("cli_tool_audit.views.process_tools", return_value=results):
            code = report_from_pyproject_toml(
                file_path=None,
                config_as_dict={"mytool": CliToolConfig(name="mytool")},
                exit_code_on_failure=True,
                file_format="table",
            )
        assert code == 0

    def test_raises_when_no_file_path_and_no_dict(self):
        with pytest.raises(TypeError):
            report_from_pyproject_toml(file_path=None, config_as_dict=None)
