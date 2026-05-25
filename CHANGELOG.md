# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- Upgrade to uv

## [3.2.0] - 2026-03-27
### Added
- GUI for discoverability and ease of use (`cli_tool_audit gui` or `cli_tool_audit-gui`)
- `discover` subcommand to scan project files (Makefile, workflows, `package.json`, Dockerfiles, shell scripts) for CLI tool references
- `--quiet` option to suppress output
- `--gui` flag as an alias for the `gui` subcommand

## [3.1.0] - 2024-08-24
### Fixed
- Ranged semver expectations were ignoring the range syntax

## [3.0.3] - 2024-08-03
### Changed
- Add `CLI_TOOL_AUDIT_USE_SHELL` environment variable to allow shell-based tool lookup for tools like pipx
- Clean up desired semver string before passing to semver checker to prevent crashes on malformed input
- Improve debug logging throughout audit manager with per-schema and per-tool log messages
- Expand test coverage for models, compatibility, and version parsing modules

## [3.0.2] - 2024-07-27
### Added
- Add compatibility improvements

## [3.0.1] - 2024-01-20
### Fixed
- More unit tests, fix link in meta, uses Path instead of str for paths

## [3.0.0] - 2024-01-20
### Fixed
- Only truncate long version on console output
- Removed three dependencies (toml, hypothesis, importlib-metadata)

### Added
- Filter an audit by tags
- install_docs, install_command to show what to do when there are problems
- `single` to validate one tool without a config file
- `.html` output

## [2.0.0] - 2024-01-19
### Fixed
- Cache now adds gitignore and clears files older than 30 days on startup
- Audit is now a sub command with arguments

### Changed
- Gnu options with dashes, no underscores
- Global opts that apply to only some commands move to subparser
- check_only_for_existence is now schema type existence, snapshot_version is now schema type snapshot
- default action is now audit with all defaults

## [1.2.0] - 2024-01-17
### Added
- Caching of good results, speeding things up
- Caching enabled only for batches of 5+ tool checks
- Formalize support of four schemas, semver, pep440, snapshot and exists
- Added about.py

### Fixed
- Wrong OS no longer flagged as problem
- Added lock to ThreadPoolExecutor's work items

## [1.1.0] - 2024-01-16
### Added
- Interactive config at cli with `--interactive`
- Short switches for cli args and aliases for - and _ as connectors
- Export multiple file formats with `--file-format`
- Added subcommand for `audit` with intention of removing default action

### Fixed
- Spelling and docs. Make file now lints docs and runs spell check tools

## [1.0.7] - 2024-01-16
### Fixed
- Spelling and docs. Make file now lints docs and runs spell check tools

## [1.0.6] - 2024-01-16
### Fixed
- Add basic_test.sh and fix issue found with it

## [1.0.5] - 2024-01-16
### Fixed
- Needs packaging lib in deps

## [1.0.4] - 2024-01-16
### Added
- Support for if_os, snapshot
- Config manager and possibility to do config via cli
- Freeze command
- Last modified

### Fixed
- Tested with tox and got passing on 3.9-3.12
- Possibly fixed dependencies

## [1.0.3] - 2024-01-15
### Added
- Support for ^, ~ and * version ranges

## [1.0.2] - 2024-01-14
### Added
- Color mode actually works now, problems are in red
- Logging and verbose switch created

### Fixed
- When calling subprocess, it now checks stderr if nothing returned by stdout

## [1.0.1] - 2024-01-14
### Added
- New stress test using npm
- Started concept of known switches

### Fixed
- All reports print with pretty tables
- Version switch always defaults to --version
- Tuple results are now dataclasses
- validate is now a function and exported

## [1.0.0] - 2024-01-14
### Added
- Application created

[Unreleased]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v3.2.0...HEAD
[3.2.0]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v3.0.3...v3.1.0
[3.0.3]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v3.0.2...v3.0.3
[3.0.2]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v3.0.1...v3.0.2
[3.0.1]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.0.7...v1.1.0
[1.0.7]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/matthewdeanmartin/cli_tool_audit/compare/v1.0.0...v1.0.1
