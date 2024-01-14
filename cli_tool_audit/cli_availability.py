"""
Check if an external tool is expected and available on the PATH.

Also, check version.

Possible things that could happen
- found/not found on path
- found but can't run without error
- found, runs but wrong version switch
- found, has version but cli version != package version
"""

import logging
import subprocess  # nosec
from dataclasses import dataclass
from typing import Optional

import toml

# pylint: disable=no-name-in-module
from whichcraft import which

from cli_tool_audit.known_swtiches import KNOWN_SWITCHES

logger = logging.getLogger(__name__)


def read_config(file_path: str) -> dict[str, dict[str, str]]:
    """
    Read the cli-tools section from a pyproject.toml file.

    Args:
        file_path (str): The path to the pyproject.toml file.

    Returns:
        dict[str, dict[str, str]]: A dictionary with the cli-tools section.
    """
    # pylint: disable=broad-exception-caught
    try:
        with open(file_path, encoding="utf-8") as file:
            pyproject_data = toml.load(file)
        return pyproject_data.get("tool", {}).get("cli-tools", {})
    except BaseException as e:
        logger.error(e)
        print(f"Error reading pyproject.toml: {e}")
        return {}


@dataclass
class ToolAvailabilityResult:
    is_available: bool
    is_broken: bool
    version: Optional[str]


def check_tool_availability(tool_name: str, version_switch: str = "--version") -> ToolAvailabilityResult:
    """
    Check if a tool is available in the system's PATH.

    Args:
        tool_name (str): The name of the tool to check.
        version_switch (str): The switch to get the tool version. Defaults to '--version'.

    Returns:
        ToolAvailabilityResult: An object containing the availability and version of the tool.
    """
    # Check if the tool is in the system's PATH
    is_broken = True
    if not which(tool_name):
        return ToolAvailabilityResult(False, True, None)

    if version_switch is None or version_switch == "--version":
        # override default.
        # Could be a problem if KNOWN_SWITCHES was ever wrong.
        version_switch = KNOWN_SWITCHES.get(tool_name, "--version")

    version = None

    # pylint: disable=broad-exception-caught
    try:
        result = subprocess.run(
            [tool_name, version_switch], capture_output=True, text=True, timeout=5, shell=False, check=True
        )  # nosec
        out = result.stdout.strip()
        if "\n" in out:
            version = out.split("\n")[0]
        else:
            version = result.stdout.strip()
        is_broken = False
    except BaseException as exception:
        is_broken = True
        # TODO: run help and parse that?
        # logger.error(exception)
        print(exception)

    return ToolAvailabilityResult(True, is_broken, version)


if __name__ == "__main__":

    def run() -> None:
        """Example"""
        # Example usage
        file_path = "../pyproject.toml"
        cli_tools = read_config(file_path)

        for tool, config in cli_tools.items():
            result = check_tool_availability(tool, config.get("version_switch", "--version"))
            print(
                f"{tool}: {'Available' if result.is_available else 'Not Available'}"
                f" - Version:\n{result.version if result.version else 'N/A'}"
            )

    run()
