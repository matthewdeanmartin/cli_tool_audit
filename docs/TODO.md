# TODO

## Docs

- examples in epilogue for each subcommand
- Separate out the huge subcommand --help text with examples

## policies

- pass if found, even if broken - DONE.
- pass if found and not broken, but not version number. - TODO
- pass only if found and not broken and version number is compatible - DONE.

## features

- Freeze
- import from known formats, e.g. pyproject.toml, cargo.toml, etc.

## Build

- dog fooding: check against current app (pyproject vs --version), i.e. dogfooding, let cli_tool_audit check if
  verstrings are right. FAILED. subprocess.run() can't see the cli command

## version sources

- fall back to windows file attribute (requires windows support! win32 api calls and MS 4 part versions)
- fall back to known ecosystem, e.g. pyproject, cargo, etc. (e.g. running pip info or the like to get a version)

## Logging/Debug

- `--quiet` Just return code?
- `--log-level`  # debug, info, warning, error, critical

## Tests

- include some tools that don't exist
- These scenarios: https://packaging.python.org/en/latest/specifications/version-specifiers/
