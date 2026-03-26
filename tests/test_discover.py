"""Tests for cli_tool_audit.discover module."""

import textwrap
from pathlib import Path

from cli_tool_audit.discover import (
    _scan_dockerfile,
    _scan_github_workflows,
    _scan_makefile,
    _scan_package_json,
    _scan_shell_scripts,
    discover_tools,
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


class TestScanMakefile:
    def test_extracts_recipe_tools(self, tmp_path):
        _write(
            tmp_path,
            "Makefile",
            """\
            test:
            \tpytest tests/
            \truff check .
            """,
        )
        found = _scan_makefile(tmp_path / "Makefile")
        assert "pytest" in found
        assert "ruff" in found

    def test_strips_venv_prefix(self, tmp_path):
        _write(
            tmp_path,
            "Makefile",
            """\
            lint:
            \t$(VENV) mypy cli_tool_audit
            """,
        )
        found = _scan_makefile(tmp_path / "Makefile")
        assert "mypy" in found

    def test_ignores_comments(self, tmp_path):
        _write(
            tmp_path,
            "Makefile",
            """\
            check:
            \t# echo ignored
            \tblack .
            """,
        )
        found = _scan_makefile(tmp_path / "Makefile")
        assert "echo" not in found
        assert "black" in found

    def test_missing_makefile_returns_empty(self, tmp_path):
        found = _scan_makefile(tmp_path / "Makefile")
        assert found == set()


class TestScanPackageJson:
    def test_extracts_script_tools(self, tmp_path):
        _write(
            tmp_path,
            "package.json",
            """\
            {
              "scripts": {
                "test": "jest --coverage",
                "lint": "eslint src && prettier --check src"
              }
            }
            """,
        )
        found = _scan_package_json(tmp_path / "package.json")
        assert "jest" in found
        assert "eslint" in found
        assert "prettier" in found

    def test_missing_returns_empty(self, tmp_path):
        found = _scan_package_json(tmp_path / "package.json")
        assert found == set()


class TestScanDockerfile:
    def test_extracts_run_tools(self, tmp_path):
        _write(
            tmp_path,
            "Dockerfile",
            """\
            FROM python:3.12
            RUN apt-get update && uv sync
            RUN ruff check .
            """,
        )
        found = _scan_dockerfile(tmp_path / "Dockerfile")
        assert "uv" in found
        assert "ruff" in found

    def test_missing_returns_empty(self, tmp_path):
        found = _scan_dockerfile(tmp_path / "Dockerfile")
        assert found == set()


class TestScanShellScripts:
    def test_extracts_tools_from_scripts(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "check.sh").write_text("#!/bin/bash\npytest tests/\nmypy .\n", encoding="utf-8")
        found = _scan_shell_scripts(tmp_path)
        assert "pytest" in found
        assert "mypy" in found

    def test_missing_scripts_dir_returns_empty(self, tmp_path):
        found = _scan_shell_scripts(tmp_path)
        assert found == set()


class TestScanGithubWorkflows:
    def test_extracts_run_commands(self, tmp_path):
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text(
            "jobs:\n  build:\n    steps:\n      - run: pytest tests/\n      - run: ruff check .\n",
            encoding="utf-8",
        )
        found = _scan_github_workflows(tmp_path)
        assert "pytest" in found
        assert "ruff" in found

    def test_missing_workflows_returns_empty(self, tmp_path):
        found = _scan_github_workflows(tmp_path)
        assert found == set()


class TestDiscoverTools:
    def test_aggregates_sources(self, tmp_path):
        _write(
            tmp_path,
            "Makefile",
            """\
            test:
            \tpytest tests/
            """,
        )
        result = discover_tools(tmp_path)
        assert "pytest" in result
        assert "Makefile" in result["pytest"]

    def test_tool_found_in_multiple_sources(self, tmp_path):
        _write(tmp_path, "Makefile", "test:\n\tpytest tests/\n")
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "run.sh").write_text("pytest\n", encoding="utf-8")
        result = discover_tools(tmp_path)
        assert "pytest" in result
        assert len(result["pytest"]) == 2

    def test_returns_sorted_keys(self, tmp_path):
        _write(tmp_path, "Makefile", "test:\n\tzsh_tool tests/\n\taaa_tool .\n")
        result = discover_tools(tmp_path)
        keys = list(result.keys())
        assert keys == sorted(keys)
