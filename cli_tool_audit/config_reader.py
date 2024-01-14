"""
Read list of tools from config.
"""

import logging

import toml

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
        logger.debug(f"Loading config from {file_path}")
        with open(file_path, encoding="utf-8") as file:
            pyproject_data = toml.load(file)
        found = pyproject_data.get("tool", {}).get("cli-tools", {})
        if not found:
            logger.warning("Config section not found, expect [tool.cli-tools]")
        return found
    except BaseException as e:
        logger.error(e)
        print(f"Error reading pyproject.toml: {e}")
        return {}
