"""
Main output view for cli_tool_audit assuming tool list is in config.
"""
import concurrent
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

from prettytable import PrettyTable

import cli_tool_audit.cli_availability as cli_availability
from cli_tool_audit.compatibility import check_compatibility


@dataclass
class ToolCheckResult:
    tool: str
    desired_version: str
    is_available: bool
    found_version: Optional[str]
    is_compatible: str
    is_broken: bool


def check_tool_wrapper(tool_info: tuple[str, dict[str, str]]) -> ToolCheckResult:
    """
    Wrapper function for check_tool_availability() that returns a ToolCheckResult object.

    Args:
        tool_info (tuple[str, dict[str, str]]): A tuple containing the tool name and the tool configuration.

    Returns:
        ToolCheckResult: A ToolCheckResult object.
    """
    tool, config = tool_info
    result = cli_availability.check_tool_availability(tool, config.get("version_switch", "--version"))
    desired_version = config["version"]
    is_compatible = check_compatibility(desired_version, found_version=result.version)

    return ToolCheckResult(
        tool=tool,
        desired_version=desired_version,
        is_available=result.is_available,
        found_version=result.version,
        is_compatible=is_compatible,
        is_broken=result.is_broken,
    )


def validate(file_path: str = "pyproject.toml") -> list[ToolCheckResult]:
    """
    Validate the tools in the pyproject.toml file.

    Args:
        file_path (str, optional): The path to the pyproject.toml file. Defaults to "pyproject.toml".

    Returns:
        list[ToolCheckResult]: A list of ToolCheckResult objects.
    """
    cli_tools = cli_availability.read_config(file_path)

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
    if not os.path.exists(file_path):
        one_up = os.path.join("..", file_path)
        if os.path.exists(one_up):
            file_path = one_up

    results = validate(file_path)

    failed = pretty_print_results(results)
    if failed and exit_code_on_failure:
        sys.exit(1)


def pretty_print_results(results: list[ToolCheckResult]) -> bool:
    # TODO separate out failed logic
    table = PrettyTable()
    table.field_names = ["Tool", "Found Version", "Desired Version", "Compatible", "Status"]
    # Process the results as they are completed
    failed = False
    for result in results:
        if result.is_broken:
            status = "Error on execution"
            failed = True
        elif not result.is_available:
            status = "Not available"
            failed = True
        else:
            status = "Available"
        if not result.is_compatible:
            failed = True

        table.add_row(
            [
                result.tool,
                result.found_version[0:50] if result.found_version else "N/A",
                result.desired_version,
                "Yes" if result.is_compatible == "Compatible" else "No",
                status,
            ]
        )
    # Print the table
    print(table)
    return failed


if __name__ == "__main__":
    report_from_pyproject_toml()
