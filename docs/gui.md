# GUI

cli_tool_audit includes a Tkinter-based graphical interface for users who prefer not to use the command line.

## Launching

```shell
# As a subcommand
cli_tool_audit gui

# As a flag
cli_tool_audit --gui

# As a dedicated entry point
cli_tool_audit-gui
```

## Features

The GUI provides panels for:

- **Dashboard** — overview of audit results
- **Inspect** — drill into individual tool results
- **Doctor** — diagnose configuration issues
- **Edit** — add, update, or remove tool entries
- **Freeze / Populate** — discover and snapshot current tools
- **Backup / Repair** — manage configuration files

## Notes

- The GUI requires `tkinter`, which is included with standard Python on most platforms.
- On minimal Linux installs you may need to install `python3-tk` separately.
- The GUI imports are deferred so the CLI has zero overhead when not using the GUI.
