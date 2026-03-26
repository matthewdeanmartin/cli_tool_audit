"""Extended tests for cli_tool_audit.freeze module."""

from unittest.mock import patch

from cli_tool_audit.freeze import (
    freeze_requirements,
    freeze_to_config,
    freeze_to_screen,
    infer_tools_from_makefile,
    infer_tools_from_path,
    list_path_categories,
)
from cli_tool_audit.models import SchemaType, ToolAvailabilityResult


def _unavailable_result() -> ToolAvailabilityResult:
    return ToolAvailabilityResult(is_available=False, is_broken=True, version=None, last_modified=None)


def _available_result(version="1.0.0") -> ToolAvailabilityResult:
    return ToolAvailabilityResult(is_available=True, is_broken=False, version=version, last_modified=None)


class TestFreezeRequirements:
    @patch("cli_tool_audit.freeze.call_tools.check_tool_availability")
    def test_returns_dict_of_results(self, mock_check):
        mock_check.return_value = _available_result("3.11.0")
        results = freeze_requirements(["python"], SchemaType.SNAPSHOT)
        assert "python" in results
        assert results["python"].version == "3.11.0"

    @patch("cli_tool_audit.freeze.call_tools.check_tool_availability")
    def test_unavailable_tool_included(self, mock_check):
        mock_check.return_value = _unavailable_result()
        results = freeze_requirements(["nonexistent_tool"], SchemaType.SEMVER)
        assert "nonexistent_tool" in results
        assert results["nonexistent_tool"].is_available is False

    @patch("cli_tool_audit.freeze.call_tools.check_tool_availability")
    def test_multiple_tools(self, mock_check):
        mock_check.side_effect = [_available_result("1.0"), _available_result("2.0")]
        results = freeze_requirements(["tool_a", "tool_b"], SchemaType.SNAPSHOT)
        assert len(results) == 2


class TestFreezeToConfig:
    @patch("cli_tool_audit.freeze.call_tools.check_tool_availability")
    def test_writes_available_tools_to_config(self, mock_check, tmp_path):
        mock_check.return_value = _available_result("1.2.3")
        config_path = tmp_path / "pyproject.toml"
        freeze_to_config(["mytool"], config_path, SchemaType.SNAPSHOT)
        assert config_path.exists()
        content = config_path.read_text(encoding="utf-8")
        assert "mytool" in content

    @patch("cli_tool_audit.freeze.call_tools.check_tool_availability")
    def test_skips_unavailable_tools(self, mock_check, tmp_path):
        mock_check.return_value = _unavailable_result()
        config_path = tmp_path / "pyproject.toml"
        freeze_to_config(["notfound"], config_path, SchemaType.SNAPSHOT)
        # File may or may not be created; if it is, "notfound" should not have a version entry
        if config_path.exists():
            content = config_path.read_text(encoding="utf-8")
            # No version value means the tool was not written with a version
            assert "notfound" not in content or "version" not in content


class TestFreezeToScreen:
    @patch("cli_tool_audit.freeze.call_tools.check_tool_availability")
    def test_prints_output(self, mock_check, capsys):
        mock_check.return_value = _available_result("3.11.0")
        freeze_to_screen(["python"], SchemaType.SNAPSHOT)
        captured = capsys.readouterr().out
        assert "python" in captured

    @patch("cli_tool_audit.freeze.call_tools.check_tool_availability")
    def test_unavailable_tool_not_in_output(self, mock_check, capsys):
        mock_check.return_value = _unavailable_result()
        freeze_to_screen(["ghosttool"], SchemaType.SNAPSHOT)
        captured = capsys.readouterr().out
        # Ghost tool had no version so nothing to write
        assert "ghosttool" not in captured


class TestInferToolsFromMakefile:
    def test_returns_list(self, tmp_path):
        makefile = tmp_path / "Makefile"
        makefile.write_text("test:\n\tpython --version\n", encoding="utf-8")
        result = infer_tools_from_makefile(makefile)
        assert isinstance(result, list)
        assert result == sorted(result)

    def test_missing_makefile_returns_empty(self, tmp_path):
        result = infer_tools_from_makefile(tmp_path / "Makefile")
        assert result == []

    def test_tools_not_on_path_are_excluded(self, tmp_path):
        makefile = tmp_path / "Makefile"
        makefile.write_text("test:\n\t__tool_xyz_not_on_path__ --version\n", encoding="utf-8")
        result = infer_tools_from_makefile(makefile)
        assert "__tool_xyz_not_on_path__" not in result


class TestInferToolsFromPath:
    def test_python_category_returns_list(self):
        result = infer_tools_from_path("python")
        assert isinstance(result, list)
        assert result == sorted(result)  # should be sorted

    def test_unknown_category_returns_empty(self):
        result = infer_tools_from_path("__nonexistent_category__")
        assert result == []

    def test_none_category_checks_all(self):
        result = infer_tools_from_path(None)
        assert isinstance(result, list)

    def test_no_duplicates(self):
        result = infer_tools_from_path(None)
        assert len(result) == len(set(result))


class TestListPathCategories:
    def test_returns_sorted_list(self):
        categories = list_path_categories()
        assert categories == sorted(categories)

    def test_contains_expected_categories(self):
        categories = list_path_categories()
        for expected in ("python", "node", "git", "docker"):
            assert expected in categories

    def test_returns_list_of_strings(self):
        categories = list_path_categories()
        assert all(isinstance(c, str) for c in categories)
