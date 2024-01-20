# Use Cases

## Developer Environment

Goal: Make sure developers have all the tools they need at a suitable version.

Alternative solutions: Docker files, imaged laptops, devcontainers, installing all tools with the same package manager.

### Steps

1. Freeze the versions of the tools you want to use. Developers may have different OS, and getting workstations
   exactly the same is difficult, so choose "semver" for some flexibility.

```shell
cli_tool_audit freeze python java make rustc --version semver
```

2. Copy the output into your pyproject.toml.
1. Edit the "installation_instructions" as needed
1. Developers run on their machines, or as a early step in the local build process

```shell
cli_tool_audit audit
```

## Server/Build Server Configuration Drift Detection

Goal: Know when the tool versions have drifted too far for comfort on the build server.

Alternative solutions: Docker base image that you control and upgrade on your own timeline.

1. Freeze the versions of the tools you want to use.

```shell
cli_tool_audit freeze python java make rustc --version snapshot
```

2. Copy the output into your pyproject.toml.
1. Add to build script.

```shell
cli_tool_audit audit
```

## End-User Application "pre-flight" checks

Goal: Make sure the user has the tools they need to run your application.

Alternative solutions: Bundle the other applications wiht your application.

## Steps

1. Freeze the versions of the tools you want to use.

```shell
cli_tool_audit freeze python java make rustc --version snapshot
```

2. Copy the output into your pyproject.toml or other toml file.
1. Call programmatically on startup.

```python
import cli_tool_audit

results = cli_tool_audit.validate(file_path="path/to/your/config.toml")
# Display results if there are problems.
```
