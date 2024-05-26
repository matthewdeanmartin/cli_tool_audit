"""
Argument parsing code.
"""

import argparse
import logging
import logging.config
import sys
from collections.abc import Sequence
from dataclasses import fields
from pathlib import Path
from typing import Any, Optional

import cli_tool_audit.config_manager as config_manager
import cli_tool_audit.freeze as freeze
import cli_tool_audit.interactive as interactive
import cli_tool_audit.logging_config as logging_config
import cli_tool_audit.models as models
import cli_tool_audit.view_npm_stress_test as demo_npm
import cli_tool_audit.view_pipx_stress_test as demo_pipx
import cli_tool_audit.view_venv_stress_test as demo_venv
import cli_tool_audit.views as views
from cli_tool_audit.__about__ import __description__, __version__

logger = logging.getLogger(__name__)


def handle_read(args: argparse.Namespace) -> None:
    """
    Read and list all tool configurations
    Args:
        args: The args from the command line.
    """
    manager = config_manager.ConfigManager(Path(args.config))
    manager.read_config()
    for tool, config in manager.tools.items():
        print(f"{tool}")
        for key, value in vars(config).items():
            if value is not None:
                print(f"  {key}: {value}")


def handle_create(args: argparse.Namespace) -> None:
    """
    Create a new tool configuration.
    Args:
        args: The args from the command line.
    """
    kwargs = reduce_args_tool_cli_tool_config_args(args)

    manager = config_manager.ConfigManager(Path(args.config))
    manager.create_tool_config(args.tool, kwargs)
    print(f"Tool {args.tool} created.")


def reduce_args_tool_cli_tool_config_args(args: argparse.Namespace) -> dict[str, Any]:
    """
    Reduce the args to only those that are in CliToolConfig.
    Args:
        args: The args from the command line.

    Returns:
        dict: The reduced args.
    """
    kwargs = {}
    args_dict = vars(args)
    cli_tool_fields = {f.name for f in fields(models.CliToolConfig)}
    for key, value in args_dict.items():
        if key in cli_tool_fields:
            kwargs[key] = value
    return kwargs


def handle_update(args: argparse.Namespace) -> None:
    kwargs = reduce_args_tool_cli_tool_config_args(args)
    manager = config_manager.ConfigManager(Path(args.config))
    manager.update_tool_config(args.tool, {k: v for k, v in kwargs.items() if k != "tool"})
    print(f"Tool {args.tool} updated.")


def handle_delete(args: argparse.Namespace) -> None:
    """
    Delete a tool configuration.
    Args:
        args: The args from the command line.
    """
    manager = config_manager.ConfigManager(Path(args.config))
    manager.delete_tool_config(args.tool)
    print(f"Tool {args.tool} deleted.")


def handle_interactive(args: argparse.Namespace) -> None:
    """
    Interactively edit configuration from terminal.
    Args:
        args: The args from the command line.
    """
    manager = config_manager.ConfigManager(Path(args.config))
    interactive.interactive_config_manager(manager)


def add_update_args(parser: argparse.ArgumentParser) -> None:
    """
    Add arguments to the add or update parser.
    Args:
        parser: The add or update parser.
    """
    parser.add_argument("--version", help="Version of the tool")
    parser.add_argument("--version-switch", "--version_switch", help="Version switch for the tool")
    add_schema_argument(parser)
    parser.add_argument("--if-os", help="Check only on this os.")

    # TODO: Add more arguments


def handle_audit(args: argparse.Namespace) -> None:
    """
    Audit environment with current configuration.

    Args:
        args: The args from the command line.
    """
    views.report_from_pyproject_toml(
        file_path=Path(args.config),
        exit_code_on_failure=not args.never_fail,
        file_format=args.format,
        no_cache=args.no_cache,
        tags=args.tags,
        only_errors=args.only_errors,
    )


def handle_single(args):
    """
    Audit environment with current configuration.

    Args:
        args: The args from the command line.
    """
    config = models.CliToolConfig(
        name=args.tool, version=args.version, version_switch=args.version_switch, schema=args.schema, if_os=args.if_os
    )
    views.report_from_pyproject_toml(
        file_path=None,
        config_as_dict={args.tool: config},
        exit_code_on_failure=True,
        file_format=args.format,
        no_cache=False,
        tags=None,
        only_errors=False,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse arguments and run the CLI tool.
    Args:
        argv: The arguments to parse.

    Returns:
        int: The exit code.
    """
    # Create the parser
    program = "cli_tool_audit"
    parser = argparse.ArgumentParser(
        prog=program,
        allow_abbrev=False,
        description=__description__,
        epilog=f"""
    Examples:

        # Audit and report using pyproject.toml
        {program} audit
        
        # Generate config for snapshots
        {program} freeze python java make rustc
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit.",
    )

    parser.add_argument("--verbose", action="store_true", help="verbose output")

    parser.add_argument(
        "--demo",
        type=str,
        choices=("pipx", "venv", "npm"),
        help="Demo for values of npm, pipx or venv",
    )

    subparsers = parser.add_subparsers(help="Subcommands.")

    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Interactively edit configuration")
    add_config_to_subparser(interactive_parser)
    interactive_parser.set_defaults(func=handle_interactive)

    # Add 'freeze' sub-command
    freeze_parser = subparsers.add_parser("freeze", help="Freeze the versions of specified tools")
    freeze_parser.add_argument("tools", nargs="+", help="List of tool names to freeze")
    add_schema_argument(freeze_parser)
    add_config_to_subparser(freeze_parser)

    # Add 'audit' sub-command
    audit_parser = subparsers.add_parser("audit", help="Audit environment with current configuration")
    add_formats(audit_parser)
    add_config_to_subparser(audit_parser)
    audit_parser.add_argument("-nf", "--never-fail", action="store_true", help="Never return a non-zero exit code")
    audit_parser.add_argument(
        "-nc",
        "--no-cache",
        action="store_true",
        help="Disable caching of results.",
    )
    audit_parser.add_argument(
        "-oe",
        "--only-errors",
        action="store_true",
        help="Show only tools in error.",
    )

    audit_parser.add_argument(
        "--tags",
        # action='append',
        nargs="+",
        help="Tag for filtering tools.",
    )
    audit_parser.set_defaults(func=handle_audit)

    # Single audit
    single_parser = subparsers.add_parser("single", help="Audit one tool without configuration file")
    single_parser.add_argument("tool", help="Name of the tool")
    single_parser.add_argument("--version", help="Version of the tool")
    single_parser.add_argument("--version-switch", "--version_switch", help="Version switch for the tool")
    add_schema_argument(single_parser)
    add_formats(single_parser)
    single_parser.add_argument("--if-os", help="Check only on this os.")
    single_parser.set_defaults(func=handle_single)

    # Read command
    read_parser = subparsers.add_parser("read", help="Read and list all tool configurations")
    add_config_to_subparser(read_parser)
    read_parser.set_defaults(func=handle_read)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new tool configuration")
    create_parser.add_argument("tool", help="Name of the tool")
    add_update_args(create_parser)
    add_config_to_subparser(create_parser)
    create_parser.set_defaults(func=handle_create)

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an existing tool configuration")
    update_parser.add_argument("tool", help="Name of the tool")
    add_config_to_subparser(update_parser)
    add_update_args(update_parser)

    update_parser.set_defaults(func=handle_update)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a tool configuration")
    delete_parser.add_argument("tool", help="Name of the tool")
    add_config_to_subparser(delete_parser)
    delete_parser.set_defaults(func=handle_delete)

    # --------------------------------------------------------------------------

    # Parse the arguments
    args = parser.parse_args(argv)

    if args.verbose:
        config = logging_config.generate_config(level="DEBUG")
        logging.config.dictConfig(config)
    else:
        # Essentially, quiet mode
        logging.basicConfig(level=logging.FATAL)

    logger.debug(f"command line args: {args}")

    # Demos
    if args.demo and args.demo == "pipx":
        demo_pipx.report_for_pipx_tools()
        return 0
    if args.demo and args.demo == "venv":
        demo_venv.report_for_venv_tools()
        return 0
    if args.demo and args.demo == "npm":
        demo_npm.report_for_npm_tools()
        return 0

    if hasattr(args, "func"):
        args.func(args)
        return 0

    # Namespace doesn't have word "freeze" in it.
    if hasattr(args, "tools") and args.tools:
        freeze.freeze_to_screen(args.tools, args.schema)
        return 0

    # Audit

    # Default behavior
    print("No command specified. Auditing environment with pyproject.toml configuration.")
    return views.report_from_pyproject_toml(exit_code_on_failure=True, file_format="table", no_cache=True)


def add_formats(audit_parser):
    audit_parser.add_argument(
        "-f",
        "--format",
        default="table",
        type=str,
        choices=("json", "json-compact", "xml", "table", "csv", "html"),
        help="Output results in the specified format. (default is %(default)s)",
    )


def add_schema_argument(parser):
    parser.add_argument(
        "--schema", choices=("semver", "snapshot", "pep440", "existence"), default="snapshot", help="version schema"
    )


def add_config_to_subparser(interactive_parser):
    interactive_parser.add_argument(
        "-c",
        "--config",
        default="pyproject.toml",
        type=str,
        help="Path to the configuration file in TOML format. (default is %(default)s)",
    )


if __name__ == "__main__":
    sys.exit(main(["audit"]))
