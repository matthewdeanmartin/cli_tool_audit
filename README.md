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
```
❯ cli_tool_audit --help
usage: cli_tool_audit [-h] [--version] [--config CONFIG] [--verbose] [--demo DEMO]

Audit version numbers of CLI tools.

options:
  -h, --help       show this help message and exit
  --version        Show program's version number and exit.
  --config CONFIG  Path to the configuration file in TOML format.
  --verbose        verbose output
  --demo DEMO      Demo for values of npm, pipx or venv
```

```python
import cli_tool_audit

print(cli_tool_audit.validate(config="pyproject.toml"))
```

The configuration file lists the tools you expect how hints on how detect the version.
```toml
[tool.cli-tools]
pipx = { version = "^1.0.0", version_switch = "--version" }
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

## How does this relate to package managers, e.g. apt, pipx, npm, choco, etc.

Package managers do far more than check for the existence of a tool. They will install it, at the desired version 
and make sure that tools and their transitive dependencies are compatible.

What they can't do is verify what other package managers have done.

This captures your desired tools, versions and guarantees you have them by installing them.
```shell
# list everything available on one machine
pip freeze>requirements.txt
# install it on another.
pip install -r requirements.txt
```

This is the same thing, but for windows and .net centric apps.
```shell
choco export requirements.txt
choco install -y requirements.txt
```

There are similar patterns, for apt, brew, npm, and so on.

It would be foolish to try to create a package manager that supports other package managers, so features in that 
vein are out of scope.

## Prior Art

- [tool-audit](https://github.com/jstutters/toolaudit)
- [dotnet-tool-list](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-tool-list)
