# TODO

## policies

- pass if found, even if broken
- pass if found and not broken, but not version number
- pass only if found and not broken and version number is compatible

## features
- check against current app (pyproject vs --version)
- check a list with expected vs actual --version

## version sources
- fall back to windows file attribute
- fall back to known ecosystem, e.g. pyproject, cargo, etc.