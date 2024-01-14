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

# pylint: disable=no-name-in-module
from whichcraft import which

from cli_tool_audit.config_reader import read_config
from cli_tool_audit.known_swtiches import KNOWN_SWITCHES

logger = logging.getLogger(__name__)


@dataclass
class ToolAvailabilityResult:
    """
    Dataclass for the result of checking tool availability.
    """

    is_available: bool
    is_broken: bool
    version: Optional[str]


def check_tool_availability(
    tool_name: str, version_switch: str = "--version", only_check_existence: bool = False
) -> ToolAvailabilityResult:
    """
    Check if a tool is available in the system's PATH and if possible, determine a version number.

    Args:
        tool_name (str): The name of the tool to check.
        version_switch (str): The switch to get the tool version. Defaults to '--version'.
        only_check_existence (bool): Only check if the tool exists, don't check version. Defaults to False.

    Returns:
        ToolAvailabilityResult: An object containing the availability and version of the tool.
    """
    # Check if the tool is in the system's PATH
    is_broken = True

    # This is wrong?
    if not which(tool_name):
        logger.warning(f"{tool_name} is not on path.")
        return ToolAvailabilityResult(False, True, None)
    if only_check_existence:
        logger.debug(f"{tool_name} exists, but not checking for version.")
        return ToolAvailabilityResult(True, False, None)

    if version_switch is None or version_switch == "--version":
        # override default.
        # Could be a problem if KNOWN_SWITCHES was ever wrong.
        version_switch = KNOWN_SWITCHES.get(tool_name, "--version")

    version = None

    # pylint: disable=broad-exception-caught
    try:
        command = [tool_name, version_switch]
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, shell=False, check=True)  # nosec
        # Sometimes version is on line 2 or later.
        version = result.stdout.strip()
        if not version:
            # check stderror
            logger.debug("Got nothing from stdout, checking stderror")
            version = result.stderr.strip()

        logger.debug(f"Called tool with {' '.join(command)}, got  {version}")
        is_broken = False
    except subprocess.CalledProcessError as exception:
        is_broken = True
        logger.error(f"{tool_name} failed invocation with {exception}")
        logger.error(f"{tool_name} stderr: {exception.stderr}")
        logger.error(f"{tool_name} stdout: {exception.stdout}")
    except FileNotFoundError:
        logger.error(f"{tool_name} is not on path.")
        return ToolAvailabilityResult(False, True, None)

    return ToolAvailabilityResult(True, is_broken, version)


if __name__ == "__main__":
    check_tool_availability("isort")

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
