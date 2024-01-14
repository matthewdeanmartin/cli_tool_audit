# cli_tool_audit
Verify that a list of cli tools are available. Like a requirements.txt for cli tools, but without an installer 
component. Intended to work with cli tools regardless to how they were installed, e.g. via pipx, npm, etc.

## How it works
You declare a list of cli commands and version ranges.

The tool will run `tool --version` for each tool and make best efforts to parse the result and compare it to the 
desired version range.

The tool then can either output a report with warnings or signal failure if something is missing, the wrong version 
or can't be determined.

There is no universal method for getting a version number from a CLI tool, nor is there a universal orderable 
version number system, so the outcome of many check may be limited to an existence check or exact version number check.

Here is an example run.
```
❯ cli_tool_audit
+-----------+-------------------------------------+-----------------+------------+-----------+
|    Tool   |            Found Version            | Desired Version | Compatible |   Status  |
+-----------+-------------------------------------+-----------------+------------+-----------+
|   python  |            Python 3.11.1            |     >=3.11.1    |    Yes     | Available |
|    java   | openjdk version "17.0.6" 2023-01-17 |     >=17.0.6    |    Yes     | Available |
|           |            OpenJDK Runtim           |                 |            |           |
|    make   |            GNU Make 3.81            |      >=3.81     |    Yes     | Available |
+-----------+-------------------------------------+-----------------+------------+-----------+
```

## Installation

You will need to install it to your virtual environment if tools you are looking for are in your virtual environment.
If all the tools are global then you can pipx install.

```shell
pipx install cli-tool-audit
```

## Usage

CLI usage
```shell
cli-tool-audit [--config=pyproject.toml]
```

```python
import cli_tool_audit

print(cli_tool_audit.validate(config="pyproject.toml"))
```

The configuration file lists the tools you expect how hints on how detect the version.
```toml
[tool.cli-tools]
pipx = { description = "Python package installer for applications", version = "^1.0.0", version_switch = "--version" }
mypy = { version = "^1.0.0", version_switch = "--version" }
pylint = {  version = "^1.0.0", version_switch = "--version" }
black = {  version = "^1.0.0", version_switch = "--version" }
pygount = { version = "^1.0.0", version_switch = "--version" }
ruff = { version = "^1.0.0", version_switch = "--version" }
```

Demos will discover a bunch of executables as installed in the local virtual environment, installed by pipx or 
installed by npm. It will then assume that we want the current or any version and run an audit. Since we know these 
files already exist, the failures are centered on failing to execute, failing to guess the version switch, failure 
to parse the switch or the 
tool's version switch returning a version incompatible to what the package manager reports.
```bash
cli_tool_audit --demo=pipx --verbose
cli_tool_audit --demo=venv --verbose
cli_tool_audit --demo=npm --verbose
```

## Testing

You can check that all pipx installed tools are compatible with the package-declared version. Sometimes they are not,
sometimes the tool fails to run, sometimes the tool doesn't support any known `--version` switch.

```bash
python -m cli_tool_audit.pipx_stress_test
```

You can check that all tools in the current virtual environment are at least version 0.0.0.

```bash
python -m cli_tool_audit.venv_stress_test
```

Just running the file will check anything configured in `pyproject.toml`

```bash
python -m cli_tool_audit
```

## Prior Art

If your cli tools are all installed by a package manager, you could use the package manager's manifest, e.g. 
pyproject.toml for poetry. If your CLI tools are installed by a variety of package managers, or not installed but 
just copied to a location on the PATH, then this may not help.

- [tool-audit](https://github.com/jstutters/toolaudit)
- [dotnet-tool-list](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-tool-list)
