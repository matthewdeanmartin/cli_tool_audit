"""
Argument parsing code.
"""
import argparse
import logging
import logging.config
import os
import sys
from typing import Any

from cli_tool_audit._version import __version__
from cli_tool_audit.view_npm_stress_test import report_for_npm_tools
from cli_tool_audit.view_pipx_stress_test import report_for_pipx_tools
from cli_tool_audit.view_venv_stress_test import report_for_venv_tools
from cli_tool_audit.views import report_from_pyproject_toml

logger = logging.getLogger(__name__)


def main():
    """Parse arguments and run the CLI tool."""
    # Create the parser
    parser = argparse.ArgumentParser(description="Audit version numbers of CLI tools.")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}", help="Show program's version number and exit."
    )
    parser.add_argument("--config", type=str, help="Path to the configuration file in TOML format.")
    parser.add_argument("--verbose", action="store_true", help="verbose output")

    parser.add_argument("--demo", type=str, help="Demo for values of npm, pipx or venv")

    # Parse the arguments
    args = parser.parse_args()

    if args.verbose:
        config: dict[str, Any] = {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "standard": {"format": "[%(levelname)s] %(name)s: %(message)s"},
                "colored": {
                    "()": "colorlog.ColoredFormatter",
                    "format": "%(log_color)s%(levelname)-8s%(reset)s %(green)s%(message)s",
                },
            },
            "handlers": {
                "default": {
                    "level": "DEBUG",
                    "formatter": "colored",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",  # Default is stderr
                },
            },
            "loggers": {
                "cli_tool_audit": {
                    "handlers": ["default"],
                    "level": "DEBUG",
                    "propagate": False,
                }
            },
        }
        if os.environ.get("NO_COLOR"):
            config["handlers"]["default"]["formatter"] = "standard"
        logging.config.dictConfig(config)
    else:
        # Essentially, quiet mode
        logging.basicConfig(level=logging.FATAL)

    logger.debug(f"command line args: {args}")

    # Demos
    if args.demo and args.demo == "pipx":
        report_for_pipx_tools()
        sys.exit()
    if args.demo and args.demo == "venv":
        report_for_venv_tools()
        sys.exit()
    if args.demo and args.demo == "npm":
        report_for_npm_tools()
        sys.exit()

    # Default behavior
    # Handle the configuration file argument
    if args.config:
        report_from_pyproject_toml(args.config)
    else:
        report_from_pyproject_toml()


if __name__ == "__main__":
    main()
