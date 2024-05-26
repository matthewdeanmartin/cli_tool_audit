"""
Read list of tools from config.
"""

import logging
from pathlib import Path

import cli_tool_audit.config_manager as config_manager
import cli_tool_audit.models as models

logger = logging.getLogger(__name__)


def read_config(file_path: Path) -> dict[str, models.CliToolConfig]:
    """
    Read the cli-tools section from a pyproject.toml file.

    Args:
        file_path (Path): The path to the pyproject.toml file.

    Returns:
        dict[str, models.CliToolConfig]: A dictionary with the cli-tools section.
    """
    # pylint: disable=broad-exception-caught
    try:
        logger.debug(f"Loading config from {file_path}")
        manager = config_manager.ConfigManager(file_path)
        found = manager.read_config()
        if not found:
            logger.warning("Config section not found, expected [tool.cli-tools] with values")
        return manager.tools
    except BaseException as e:
        logger.error(e)
        print(f"Error reading pyproject.toml: {e}")
        return {}
