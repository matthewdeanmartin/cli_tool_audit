# TODO

## policies

- pass if found, even if broken - DONE.
- pass if found and not broken, but not version number. - TODO
- pass only if found and not broken and version number is compatible - DONE.
- `--tag` and `--filter-tags` to restrict to just workstation, dev, prod.

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
- include some tools that don't exist
