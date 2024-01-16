# TODO

## policies

- pass if found, even if broken - DONE.
- pass if found and not broken, but not version number. - TODO
- pass only if found and not broken and version number is compatible - DONE.

## features

- check against current app (pyproject vs --version)
- check a list with expected vs actual --version

## version sources

- fall back to windows file attribute
- fall back to known ecosystem, e.g. pyproject, cargo, etc.

## Display

- Red if failed
- display capture + parsed found version

## Swiches

- "just failed"/concise

## Tests

- include some tools that don't exist
