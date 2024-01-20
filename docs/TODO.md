# TODO

## Docs

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
