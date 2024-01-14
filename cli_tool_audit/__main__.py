"""
Argument parsing code.
"""
import argparse

from cli_tool_audit._version import __version__
from cli_tool_audit.views import report_from_pyproject_toml


def main():
    """Parse arguments and run the CLI tool."""
    # Create the parser
    parser = argparse.ArgumentParser(description="Audit version numbers of CLI tools.")

    # Add the --version argument
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}", help="Show program's version number and exit."
    )

    # Add the --config argument
    parser.add_argument("--config", type=str, help="Path to the configuration file in TOML format.")

    # Parse the arguments
    args = parser.parse_args()

    # Handle the configuration file argument
    if args.config:
        report_from_pyproject_toml(args.config)
    else:
        report_from_pyproject_toml()


if __name__ == "__main__":
    main()
