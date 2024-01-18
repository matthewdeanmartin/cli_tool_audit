# TODO

## Docs
- Example configs for specific scenarios
  - workstation setup/developer tool 
  - deployed app "pre-flight" checks
  - CI config drift checks
- examples in epilogue
- Separate out the huge subcommand --help text with examples

## Split out about/metadata creation tool?
- Generate metadata for more source documents? (e.g. setup.cfg, setup.py, PEP pyproject toml meta)

## policies

- pass if found, even if broken - DONE.
- pass if found and not broken, but not version number. - TODO
- pass only if found and not broken and version number is compatible - DONE.

## features

- check against current app (pyproject vs --version), i.e. dogfooding, let cli_tool_audit check if verstrings are right.
- `--tag` and `--filter-tags` to restrict to just workstation, dev, prod tags.
- `--only-errors` to report only errors, not successful tool checks
- Entire cli check, e.g. `audit-one --tool some_tool --version 1.2.3`
- add `--config-file` to each subtool, doesn't seem to work as global option?

## version sources

- fall back to windows file attribute (requires windows support! win32 api calls and MS 4 part versions)
- fall back to known ecosystem, e.g. pyproject, cargo, etc. (e.g. running pip info or the like to get a version)

## Logging/Debug

- `--quiet` Just return code?
- '--log-level'  # debug, info, warning, error, critical

## Tests

- hypothesis testing
  - switch to pathlib so that hypothesis testing isn't against a string
- include some tools that don't exist
- These scenarios: https://packaging.python.org/en/latest/specifications/version-specifiers/ 