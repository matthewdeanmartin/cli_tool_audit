"""
Main output view for cli_tool_audit assuming tool list is in config.
"""
import concurrent
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import colorama
from prettytable import PrettyTable
from prettytable.colortable import ColorTable, Themes

from cli_tool_audit.call_and_compatible import ToolCheckResult, check_tool_wrapper
from cli_tool_audit.config_reader import read_config

colorama.init(convert=True)

logger = logging.getLogger(__name__)


def validate(file_path: str = "pyproject.toml") -> list[ToolCheckResult]:
    """
    Validate the tools in the pyproject.toml file.

    Args:
        file_path (str, optional): The path to the pyproject.toml file. Defaults to "pyproject.toml".

    Returns:
        list[ToolCheckResult]: A list of ToolCheckResult objects.
    """
    cli_tools = read_config(file_path)

    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    # Create a ThreadPoolExecutor with one thread per CPU
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        # Submit tasks to the executor
        futures = [executor.submit(check_tool_wrapper, (tool, config)) for tool, config in cli_tools.items()]
        results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
    return results


def report_from_pyproject_toml(file_path: str = "pyproject.toml", exit_code_on_failure: bool = True):
    """
    Report on the compatibility of the tools in the pyproject.toml file.

    Args:
        file_path (str, optional): The path to the pyproject.toml file. Defaults to "pyproject.toml".
        exit_code_on_failure (bool, optional): If True, exit with return value of 1 if validation fails. Defaults to True.
    """
    if not os.path.exists(file_path):
        one_up = os.path.join("..", file_path)
        if os.path.exists(one_up):
            file_path = one_up

    results = validate(file_path)

    failed = pretty_print_results(results)
    if failed and exit_code_on_failure:
        print("Did not pass validation, failing with return value of 1.")
        sys.exit(1)


def pretty_print_results(results: list[ToolCheckResult]) -> bool:
    """
    Pretty print the results of the validation.

    Args:
        results (list[ToolCheckResult]): A list of ToolCheckResult objects.

    Returns:
        bool: True if any of the tools failed validation, False otherwise.
    """
    # TODO separate out failed logic

    if os.environ.get("NO_COLOR"):
        table = PrettyTable()
    else:
        table = ColorTable(theme=Themes.OCEAN)
    table.field_names = ["Tool", "Found", "Parsed", "Desired", "Compatible", "Status", "Modified"]
    # Process the results as they are completed
    failed = False
    all_rows: list[list[str]] = []
    for result in results:
        if result.is_broken:
            status = "Can't run"
            failed = True
        elif not result.is_available:
            status = "Not available"
            failed = True
        else:
            status = "Available"
        if not result.is_compatible:
            failed = True

        row_data = [
            result.tool,
            result.found_version[0:25].strip() if result.found_version else "",
            result.parsed_version if result.parsed_version else "",
            result.desired_version,
            "Yes" if result.is_compatible == "Compatible" else result.is_compatible,
            status,
            result.last_modified.strftime("%m/%d/%y") if result.last_modified else "",
        ]
        row_transformed = []
        for datum in row_data:
            if result.is_compatible != "Compatible" or not result.is_available:
                transformed = f"{colorama.Fore.RED}{datum}{colorama.Style.RESET_ALL}"
            else:
                transformed = str(datum)
            row_transformed.append(transformed)
        all_rows.append(row_transformed)

    table.add_rows(sorted(all_rows, key=lambda x: x[0]))

    # Print the table
    print(table)

    return failed


if __name__ == "__main__":
    report_from_pyproject_toml()
