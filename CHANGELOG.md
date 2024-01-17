# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2024-01-17

### Added
- Caching of good results, speeding things up
- Caching enabled only for batches of 5+ tool checks
- TODO: command to clear cache/change cache location
- Formalize support of four schemas, semver, pep440, snapshot and exists.
- Added `about.py`

### Fixed
- "wrong OS" no longer flagged as problem
- Added lock to ThreadPoolExecutor's work items

## [1.1.0] - 2024-01-16

### Added
- Interactive config at cli with `--interactive`
- Short switches for cli args and aliases for - and _ as connectors
- Export multiple file formats with `--file-format`
- Added subcommand for `audit` with intention of removing default action.

### Fixed
- Spelling and docs. Make file now lints docs and runs spell check tools.

## [1.0.7] - 2024-01-16

### Fixed
- Spelling and docs. Make file now lints docs and runs spell check tools.


## [1.0.6] - 2024-01-15

### Fixed
- Add "basic_test.sh" and fix issue found with it.


## [1.0.5] - 2024-01-15

### Fixed
- Needs packaging lib in deps

## [1.0.4] - 2024-01-14

### Added
- Support for if_os, snapshot
- Config manager and possibility to do config via cli
- Freeze command
- Last modified

### Fixed
- Tested with tox and got passing on 3.9-3.12
- Possibly fixed dependencies.

## [1.0.3] - 2024-01-14

### Added
- Support for ^, ~ and * version ranges.

## [1.0.2] - 2024-01-14

### Added
- Color mode actually works now, problems are in red.
- Logging and verbose switch created

### Fixed
- When calling subprocess, it now checks stderr if nothing returned by stdout


## [1.0.1] - 2024-01-13

### Added
- New stress test using npm.
- Started concept of "known switches"

### Fixed

- All reports print with pretty tables
- Version switch always defaults to `--version`
- Tuple results are now dataclasses
- validate is now a function and exported

## [1.0.0] - 2024-01-13

### Added

- Application created.

