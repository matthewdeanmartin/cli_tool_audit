"""Tests for cli_tool_audit.config_reader module."""

from cli_tool_audit.config_reader import read_config
from cli_tool_audit.models import CliToolConfig, SchemaType


def test_read_config_from_valid_toml(tmp_path):
    toml_content = """\
[tool.cli-tools]
python = {version = ">=3.11.0", schema = "semver"}
"""
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(toml_content, encoding="utf-8")

    result = read_config(config_file)
    assert "python" in result
    assert isinstance(result["python"], CliToolConfig)
    assert result["python"].version == ">=3.11.0"
    assert result["python"].schema == SchemaType.SEMVER


def test_read_config_missing_file_returns_empty_dict(tmp_path):
    result = read_config(tmp_path / "nonexistent.toml")
    assert result == {}


def test_read_config_empty_cli_tools_section(tmp_path):
    toml_content = "[tool.cli-tools]\n"
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(toml_content, encoding="utf-8")

    result = read_config(config_file)
    assert result == {}


def test_read_config_invalid_toml_returns_empty_dict_and_prints(tmp_path, capsys):
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("this is not valid toml @@@@", encoding="utf-8")

    result = read_config(config_file)
    assert result == {}
    captured = capsys.readouterr().out
    assert "Error" in captured


def test_read_config_multiple_tools(tmp_path):
    toml_content = """\
[tool.cli-tools]
git = {schema = "semver"}
docker = {schema = "existence"}
"""
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(toml_content, encoding="utf-8")

    result = read_config(config_file)
    assert len(result) == 2
    assert "git" in result
    assert "docker" in result


def test_read_config_existence_schema(tmp_path):
    toml_content = """\
[tool.cli-tools]
make = {schema = "existence"}
"""
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(toml_content, encoding="utf-8")

    result = read_config(config_file)
    assert result["make"].schema == SchemaType.EXISTENCE


def test_read_config_deprecated_only_check_existence(tmp_path):
    toml_content = """\
[tool.cli-tools]
make = {only_check_existence = true}
"""
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(toml_content, encoding="utf-8")

    result = read_config(config_file)
    assert result["make"].schema == SchemaType.EXISTENCE


def test_read_config_deprecated_version_snapshot(tmp_path):
    toml_content = """\
[tool.cli-tools]
make = {version_snapshot = "GNU Make 4.3"}
"""
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(toml_content, encoding="utf-8")

    result = read_config(config_file)
    assert result["make"].schema == SchemaType.SNAPSHOT
    assert result["make"].version == "GNU Make 4.3"
