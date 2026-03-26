# cli_tool_audit

Verify that CLI tools are installed at compatible versions. Works regardless of how tools were installed (pipx, npm, apt, brew, choco, etc.).

## Installation

```shell
pipx install cli-tool-audit
```

Or into a virtual environment:

```shell
pip install cli-tool-audit
```

## Quick Start

Generate a config snapshot for tools you use:

```shell
cli_tool_audit freeze python java make rustc
```

Copy the output into `pyproject.toml`, then audit:

```shell
cli_tool_audit audit
```

Example output:

```text
+--------+--------------------------+--------+----------+------------+----------+
|  Tool  |          Found           | Parsed | Desired  |   Status   | Modified |
+--------+--------------------------+--------+----------+------------+----------+
|  java  | openjdk version "17.0.6" | 17.0.6 | >=17.0.6 | Compatible | 01/18/23 |
|  make  |      GNU Make 3.81       | 3.81.0 |  >=3.81  | Compatible | 11/24/06 |
| python |      Python 3.11.1       | 3.11.1 | >=3.11.1 | Compatible | 01/13/24 |
+--------+--------------------------+--------+----------+------------+----------+
```

## Configuration

Add tool declarations to `pyproject.toml`:

```toml
[tool.cli-tools]
# Semver range
pipx = { version = ">=1.0.0" }
# OS-specific
brew = { version = ">=0.1.0", if_os = "darwin" }
# Snapshot (exact output match)
poetry = { version = "Poetry (version 1.5.1)", schema = "snapshot" }
# Existence only
notepad = { schema = "existence" }
# Any version
vulture = { version = "*" }
# Caret / tilde ranges
shellcheck = { version = "^0.8.0" }
```

## All Commands

```text
usage: cli_tool_audit [-h] [-V] [--verbose] [--quiet] [--gui]
                      [--demo {pipx,venv,npm}]
                      {gui,interactive,discover,freeze,audit,single,read,create,update,delete} ...

positional arguments:
  gui           Launch the graphical interface
  interactive   Interactively edit configuration
  discover      Scan project files for CLI tool references
  freeze        Freeze the versions of specified tools
  audit         Audit environment with current configuration
  single        Audit one tool without configuration file
  read          Read and list all tool configurations
  create        Create a new tool configuration
  update        Update an existing tool configuration
  delete        Delete a tool configuration
```

## Programmatic Usage

```python
import cli_tool_audit

results = cli_tool_audit.validate(file_path="pyproject.toml")
print(results)
```

## Version Schemas

| Schema       | Description                                      |
|--------------|--------------------------------------------------|
| `semver`     | Semver range (default). Supports `>=`, `^`, `~`, `*`. |
| `pep440`     | PEP 440 version ranges (Python-style).           |
| `snapshot`   | Exact string match of `--version` output.        |
| `existence`  | Only checks if the tool is on PATH.              |
