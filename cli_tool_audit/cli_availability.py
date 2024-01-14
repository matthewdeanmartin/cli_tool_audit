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
from typing import Optional

import toml
from whichcraft import which

logger = logging.getLogger(__name__)


def read_cli_tools_from_pyproject(file_path: str) -> dict[str, dict[str, str]]:
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


def check_tool_availability(tool_name: str, version_switch: Optional[str] = None):
    """
    Check if a tool is available in the system's PATH.

    Args:
        tool_name (str): The name of the tool to check.
        version_switch (Optional[str]): The switch to get the tool version. Defaults to None.

    Returns:
        Tuple[bool, Optional[str]]: A tuple with the first element being True if the tool is available, False otherwise.
            The second element is the tool version if version_switch is provided, None otherwise.
    """
    # Check if the tool is in the system's PATH
    is_broken = True
    if not which(tool_name):
        return False, True, None

    # If version_switch is provided, try to get the version
    version = None
    if version_switch:
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

    return True, is_broken, version


if __name__ == "__main__":

    def run() -> None:
        """Example"""
        # Example usage
        file_path = "../pyproject.toml"  # Replace with the path to your pyproject.toml
        cli_tools = read_cli_tools_from_pyproject(file_path)

        for tool, config in cli_tools.items():
            is_available, is_broken, version = check_tool_availability(tool, config.get("version_switch"))
            print(
                f"{tool}: {'Available' if is_available else 'Not Available'} - Version:\n{version if version else 'N/A'}"
            )

    run()
