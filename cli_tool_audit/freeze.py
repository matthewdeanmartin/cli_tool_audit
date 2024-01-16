"""
Capture current version of a list of tools.
"""
import os
import tempfile

import cli_tool_audit.call_tools as call_tools
from cli_tool_audit.config_manager import ConfigManager


def freeze_requirements(tool_names: list[str]) -> dict[str, call_tools.ToolAvailabilityResult]:
    """
    Capture the current version of a list of tools.

    Args:
        tool_names (list[str]): A list of tool names.

    Returns:
        dict[str, call_tools.ToolAvailabilityResult]: A dictionary of tool names and versions.
    """
    results = {}
    for tool_name in tool_names:
        result = call_tools.check_tool_availability(tool_name, "--version")
        results[tool_name] = result
    return results


def freeze_to_config(tool_names: list[str], config_path: str) -> None:
    """
    Capture the current version of a list of tools and write them to a config file.

    Args:
        tool_names (list[str]): A list of tool names.
        config_path (str): The path to the config file.
    """
    results = freeze_requirements(tool_names)
    config_manager = ConfigManager(config_path)
    config_manager.read_config()
    for tool_name, result in results.items():
        if result.is_available and result.version:
            config_manager.create_update_tool_config(tool_name, {"version_snapshot": result.version})


def freeze_to_screen(tool_names: list[str]) -> None:
    """
    Capture the current version of a list of tools, write them to a temp config file,
    and print the 'cli-tools' section of the config.

    Args:
        tool_names (list[str]): A list of tool names.
    """
    results = freeze_requirements(tool_names)

    # Create a temporary directory and file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = os.path.join(temp_dir, "temp.toml")
        config_manager = ConfigManager(temp_config_path)
        config_manager.read_config()

        for tool_name, result in results.items():
            if result.is_available and result.version:
                config_manager.create_update_tool_config(tool_name, {"version_snapshot": result.version})

        # Save the config
        # pylint: disable=protected-access
        config_manager._save_config()

        # Read and print the content of the config file
        with open(temp_config_path, encoding="utf-8") as file:
            config_content = file.read()
            print(config_content)


if __name__ == "__main__":
    freeze_to_screen(["python", "pip", "poetry"])
