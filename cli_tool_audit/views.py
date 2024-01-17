"""
Main output view for cli_tool_audit assuming tool list is in config.
"""
import concurrent
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import colorama
from prettytable import PrettyTable
from prettytable.colortable import ColorTable, Themes

import cli_tool_audit.config_reader as config_reader
import cli_tool_audit.policy as policy
from cli_tool_audit.call_and_compatible import ToolCheckResult, check_tool_wrapper
from cli_tool_audit.json_utils import custom_json_serializer

colorama.init(convert=True)

logger = logging.getLogger(__name__)


def validate(file_path: str = "pyproject.toml", no_cache: bool = False) -> list[ToolCheckResult]:
    """
    Validate the tools in the pyproject.toml file.

    Args:
        file_path (str, optional): The path to the pyproject.toml file. Defaults to "pyproject.toml".
        no_cache (bool, optional): If True, don't use the cache. Defaults to False.

    Returns:
        list[ToolCheckResult]: A list of ToolCheckResult objects.
    """
    cli_tools = config_reader.read_config(file_path)

    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    enable_cache = len(cli_tools) >= 5
    # Create a ThreadPoolExecutor with one thread per CPU
    lock = Lock()
    if no_cache:
        enable_cache = False
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        # Submit tasks to the executor
        futures = [
            executor.submit(check_tool_wrapper, (tool, config, lock, enable_cache))
            for tool, config in cli_tools.items()
        ]
        results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
    return results


def report_from_pyproject_toml(
    file_path: str = "pyproject.toml",
    exit_code_on_failure: bool = True,
    file_format: str = "table",
    no_cache: bool = False,
) -> int:
    """
    Report on the compatibility of the tools in the pyproject.toml file.

    Args:
        file_path (str, optional): The path to the pyproject.toml file. Defaults to "pyproject.toml".
        exit_code_on_failure (bool, optional): If True, exit with return value of 1 if validation fails. Defaults to True.
        file_format (str, optional): The format of the output. Defaults to "table".
        no_cache (bool, optional): If True, don't use the cache. Defaults to False.

    Returns:
        int: The exit code.
    """
    if not file_format:
        file_format = "table"

    if not os.path.exists(file_path):
        one_up = os.path.join("..", file_path)
        if os.path.exists(one_up):
            file_path = one_up

    results = validate(file_path, no_cache=no_cache)

    failed = policy.apply_policy(results)
    if file_format == "json":
        print(json.dumps([result.__dict__ for result in results], indent=4, default=custom_json_serializer))
    elif file_format == "json-compact":
        print(json.dumps([result.__dict__ for result in results], default=custom_json_serializer))
    elif file_format == "xml":
        print("<results>")
        for result in results:
            print("  <result>")
            for key, value in result.__dict__.items():
                print(f"    <{key}>{value}</{key}>")
            print("  </result>")
        print("</results>")
    elif file_format == "table":
        pretty_print_results(results)
    elif file_format == "csv":
        print(
            "tool,desired_version,is_available,is_snapshot,found_version,parsed_version,is_compatible,is_broken,last_modified"
        )
        for result in results:
            print(
                f"{result.tool},{result.desired_version},{result.is_available},{result.is_snapshot},{result.found_version},{result.parsed_version},{result.is_compatible},{result.is_broken},{result.last_modified}"
            )
    else:
        print(
            f"Unknown file format: {file_format}, defaulting to table output. Supported formats: json, json-compact, xml, table, csv."
        )
        pretty_print_results(results)

    if failed and exit_code_on_failure and file_format == "table":
        print("Did not pass validation, failing with return value of 1.")
        return 1
    return 0


def pretty_print_results(results: list[ToolCheckResult]) -> None:
    """
    Pretty print the results of the validation.

    Args:
        results (list[ToolCheckResult]): A list of ToolCheckResult objects.
    """
    if os.environ.get("NO_COLOR"):
        table = PrettyTable()
    else:
        table = ColorTable(theme=Themes.OCEAN)
    table.field_names = ["Tool", "Found", "Parsed", "Desired", "Compatible", "Status", "Modified"]

    all_rows: list[list[str]] = []
    for result in results:
        if result.is_broken:
            status = "Can't run"
        elif not result.is_available:
            status = "Not available"
        else:
            status = "Available"

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
            if result.is_problem():
                transformed = f"{colorama.Fore.RED}{datum}{colorama.Style.RESET_ALL}"
            else:
                transformed = str(datum)
            row_transformed.append(transformed)
        all_rows.append(row_transformed)

    table.add_rows(sorted(all_rows, key=lambda x: x[0]))

    # Print the table
    print(table)


if __name__ == "__main__":
    report_from_pyproject_toml()
