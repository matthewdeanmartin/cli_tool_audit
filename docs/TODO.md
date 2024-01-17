# TODO

## policies

- pass if found, even if broken - DONE.
- pass if found and not broken, but not version number. - TODO
- pass only if found and not broken and version number is compatible - DONE.
- `--tag` and `--filter-tags` to restrict to just workstation, dev, prod.

## features

- check against current app (pyproject vs --version)
- check a list with expected vs actual --version
- interactive config (if bot writes it for me)

## version sources

- fall back to windows file attribute
- fall back to known ecosystem, e.g. pyproject, cargo, etc.

## Output

- --format \[json, yaml, csv, ascii\] for final report

## Switches

- `--quiet` Just return code?
- '--log-level'  # debug, info, warning, error, critical

## Tests

- include some tools that don't exist
