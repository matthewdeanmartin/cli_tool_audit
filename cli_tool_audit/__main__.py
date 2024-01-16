"""
Argument parsing code.
"""
import argparse
import logging
import logging.config
import os
import sys
from dataclasses import fields
from typing import Any

from cli_tool_audit._version import __version__
from cli_tool_audit.config_manager import CliToolConfig, ConfigManager
from cli_tool_audit.freeze import freeze_to_screen
from cli_tool_audit.view_npm_stress_test import report_for_npm_tools
from cli_tool_audit.view_pipx_stress_test import report_for_pipx_tools
from cli_tool_audit.view_venv_stress_test import report_for_venv_tools
from cli_tool_audit.views import report_from_pyproject_toml

logger = logging.getLogger(__name__)


def handle_read(args):
    config_manager = ConfigManager(args.config)
    config_manager.read_config()
    for tool, config in config_manager.tools.items():
        print(f"{tool}")
        for key, value in vars(config).items():
            if key == "only_check_existence" and value is False:
                pass
            elif value is not None:
                print(f"  {key}: {value}")


def handle_create(args):
    kwargs = reduce_args_tool_cli_tool_config_args(args)

    config_manager = ConfigManager(args.config)
    config_manager.create_tool_config(args.tool, kwargs)
    print(f"Tool {args.tool} created.")


def reduce_args_tool_cli_tool_config_args(args):
    kwargs = {}
    args_dict = vars(args)
    cli_tool_fields = {f.name for f in fields(CliToolConfig)}
    for key, value in args_dict.items():
        if key in cli_tool_fields:
            kwargs[key] = value
    return kwargs


def handle_update(args):
    kwargs = reduce_args_tool_cli_tool_config_args(args)
    config_manager = ConfigManager(args.config)
    config_manager.update_tool_config(args.tool, {k: v for k, v in kwargs.items() if k != "tool"})
    print(f"Tool {args.tool} updated.")


def handle_delete(args):
    config_manager = ConfigManager(args.config)
    config_manager.delete_tool_config(args.tool)
    print(f"Tool {args.tool} deleted.")


def main() -> None:
    """Parse arguments and run the CLI tool."""
    # Create the parser
    parser = argparse.ArgumentParser(description="Audit version numbers of CLI tools.")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}", help="Show program's version number and exit."
    )
    parser.add_argument(
        "--config", default="pyproject.toml", type=str, help="Path to the configuration file in TOML format."
    )
    parser.add_argument("--never_fail", action="store_true", help="Never return a non-zero exit code")
    parser.add_argument("--verbose", action="store_true", help="verbose output")

    parser.add_argument("--demo", type=str, help="Demo for values of npm, pipx or venv")

    subparsers = parser.add_subparsers(help="commands")

    # Read command
    read_parser = subparsers.add_parser("read", help="Read and list all tool configurations")
    read_parser.set_defaults(func=handle_read)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new tool configuration")
    create_parser.add_argument("tool", help="Name of the tool")
    create_parser.add_argument("--version", help="Version of the tool")
    create_parser.add_argument("--version_switch", nargs="?", help="Version switch for the tool")
    create_parser.add_argument(
        "--only_check_existence", action="store_true", help="Check only the existence of the tool"
    )
    # ... add other arguments as needed
    create_parser.set_defaults(func=handle_create)

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an existing tool configuration")
    update_parser.add_argument("tool", help="Name of the tool")
    update_parser.add_argument("--version", help="Version of the tool")
    update_parser.add_argument("--version_switch", help="Version switch for the tool")
    update_parser.add_argument("--version_snapshot", help="Entire capture of version is version string.")
    update_parser.add_argument("--if_os", help="Check only on this os.")
    update_parser.add_argument(
        "--only_check_existence", action="store_true", help="Check only the existence of the tool"
    )

    # TODO:
    # schema: Optional[str] = None
    # if_os: Optional[str] = None
    # version_stamp: Optional[str] = None
    # source: Optional[str] = None

    update_parser.set_defaults(func=handle_update)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a tool configuration")
    delete_parser.add_argument("tool", help="Name of the tool")
    delete_parser.set_defaults(func=handle_delete)

    # Add 'freeze' sub-command
    freeze_parser = subparsers.add_parser("freeze", help="Freeze the versions of specified tools")
    freeze_parser.add_argument("tools", nargs="+", help="List of tool names to freeze")

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

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
        sys.exit()
    # else:
    #     parser.print_help()

    # Namespace doesn't have word "freeze" in it.
    if hasattr(args, "tools") and args.tools:
        freeze_to_screen(args.tools)
        sys.exit()

    # Default behavior
    # Handle the configuration file argument
    if args.config:
        report_from_pyproject_toml(args.config, exit_code_on_failure=not args.never_fail)
    else:
        report_from_pyproject_toml(exit_code_on_failure=not args.never_fail)


if __name__ == "__main__":
    main()
