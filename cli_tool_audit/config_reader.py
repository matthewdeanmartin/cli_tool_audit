"""
Read list of tools from config.
"""

import logging

from cli_tool_audit.config_manager import ConfigManager
from cli_tool_audit.models import CliToolConfig

logger = logging.getLogger(__name__)


def read_config(file_path: str) -> dict[str, CliToolConfig]:
    """
    Read the cli-tools section from a pyproject.toml file.

    Args:
        file_path (str): The path to the pyproject.toml file.

    Returns:
        dict[str, CliToolConfig]: A dictionary with the cli-tools section.
    """
    # pylint: disable=broad-exception-caught
    try:
        logger.debug(f"Loading config from {file_path}")
        manager = ConfigManager(file_path)
        found = manager.read_config()
        if not found:
            logger.warning("Config section not found, expected [tool.cli-tools] with values")
        return manager.tools
    except BaseException as e:
        logger.error(e)
        print(f"Error reading pyproject.toml: {e}")
        return {}
