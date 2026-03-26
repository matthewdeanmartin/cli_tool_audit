"""
Capture current version of a list of tools.
"""

import os
import shutil
import tempfile
from pathlib import Path

import cli_tool_audit.call_tools as call_tools
import cli_tool_audit.config_manager as cm
import cli_tool_audit.models as models

# Broad categories of tools on PATH for --from-path --category
_PATH_CATEGORIES: dict[str, list[str]] = {
    "python": [
        "python",
        "python3",
        "pip",
        "pip3",
        "uv",
        "poetry",
        "ruff",
        "mypy",
        "black",
        "isort",
        "pytest",
        "hatch",
        "pipx",
        "tox",
        "nox",
        "pdm",
    ],
    "node": ["node", "npm", "npx", "yarn", "pnpm", "bun"],
    "java": ["java", "javac", "mvn", "gradle", "kotlin"],
    "rust": ["rustc", "cargo", "rustfmt", "clippy"],
    "go": ["go", "gofmt", "golint", "staticcheck"],
    "ruby": ["ruby", "gem", "bundle", "rake"],
    "docker": ["docker", "docker-compose", "podman", "buildah"],
    "cloud": ["aws", "gcloud", "az", "kubectl", "helm", "terraform", "pulumi"],
    "build": ["make", "cmake", "ninja", "just", "bazel", "buck"],
    "git": ["git", "gh", "hub", "git-lfs"],
    "lint": ["shellcheck", "hadolint", "yamllint", "markdownlint", "eslint", "prettier"],
    "security": ["trivy", "snyk", "bandit", "safety"],
}


def freeze_requirements(tool_names: list[str], schema: models.SchemaType) -> dict[str, models.ToolAvailabilityResult]:
    """
    Capture the current version of a list of tools.

    Args:
        tool_names (list[str]): A list of tool names.
        schema (SchemaType): The schema to use for the version.

    Returns:
        dict[str, call_tools.ToolAvailabilityResult]: A dictionary of tool names and versions.
    """
    results = {}
    for tool_name in tool_names:
        result = call_tools.check_tool_availability(tool_name, schema, "--version")
        results[tool_name] = result
    return results


def freeze_to_config(tool_names: list[str], config_path: Path, schema: models.SchemaType) -> None:
    """
    Capture the current version of a list of tools and write them to a config file.

    Args:
        tool_names (list[str]): A list of tool names.
        config_path (Path): The path to the config file.
        schema (SchemaType): The schema to use for the version.
    """
    results = freeze_requirements(tool_names, schema=schema)
    config_manager = cm.ConfigManager(config_path)
    config_manager.read_config()
    for tool_name, result in results.items():
        if result.is_available and result.version:
            config_manager.create_update_tool_config(tool_name, {"version": result.version})


def freeze_to_screen(tool_names: list[str], schema: models.SchemaType) -> None:
    """
    Capture the current version of a list of tools, write them to a temp config file,
    and print the 'cli-tools' section of the config.

    Args:
        tool_names (list[str]): A list of tool names.
        schema (SchemaType): The schema to use for the version.
    """
    results = freeze_requirements(tool_names, schema=schema)

    # Create a temporary directory and file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = os.path.join(temp_dir, "temp.toml")
        config_manager = cm.ConfigManager(Path(temp_config_path))
        config_manager.read_config()

        for tool_name, result in results.items():
            if result.is_available and result.version:
                config_manager.create_update_tool_config(tool_name, {"version": result.version})

        # Save the config
        # pylint: disable=protected-access
        config_manager._save_config()

        # Read and print the content of the config file
        with open(temp_config_path, encoding="utf-8") as file:
            config_content = file.read()
            print(config_content)


def infer_tools_from_makefile(makefile_path: Path | None = None) -> list[str]:
    """
    Discover tool names referenced in a Makefile and return those present on PATH.

    Args:
        makefile_path: Path to the Makefile. Defaults to ./Makefile in cwd.

    Returns:
        Sorted list of tool names found in the Makefile that exist on PATH.
    """
    from cli_tool_audit.discover import _scan_makefile  # local import to avoid cycles

    if makefile_path is None:
        makefile_path = Path.cwd() / "Makefile"
    found = _scan_makefile(makefile_path)
    return sorted(t for t in found if shutil.which(t))


def infer_tools_from_path(category: str | None = None) -> list[str]:
    """
    Return tools from PATH that match a known category (or all categories).

    Args:
        category: One of the known category names, or None to check everything.

    Returns:
        Sorted list of tool names present on PATH.
    """
    if category is not None:
        candidates = _PATH_CATEGORIES.get(category, [])
    else:
        candidates = [tool for tools in _PATH_CATEGORIES.values() for tool in tools]
    return sorted({t for t in candidates if shutil.which(t)})


def list_path_categories() -> list[str]:
    """Return the available category names for --from-path."""
    return sorted(_PATH_CATEGORIES.keys())


if __name__ == "__main__":
    freeze_to_screen(["python", "pip", "poetry"], schema=models.SchemaType.SNAPSHOT)
