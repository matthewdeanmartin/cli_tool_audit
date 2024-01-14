import concurrent
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from prettytable import PrettyTable

import cli_tool_audit.cli_availability as cli_availability
from cli_tool_audit.compatibility import check_compatibility


def check_tool_wrapper(tool_info: tuple[str, dict[str, str]]):
    tool, config = tool_info
    is_available, is_broken, found_version = cli_availability.check_tool_availability(
        tool, config.get("version_switch")
    )
    desired_version = config["version"]
    is_compatible = check_compatibility(desired_version, found_version)
    return tool, desired_version, is_available, found_version, is_compatible, is_broken


def report_from_pyproject_toml(file_path: str = "pyproject.toml", exit_code_on_failure: bool = True):
    if not os.path.exists(file_path):
        one_up = os.path.join("..", file_path)
        if os.path.exists(one_up):
            file_path = one_up

    cli_tools = cli_availability.read_cli_tools_from_pyproject(file_path)

    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    # Create a ThreadPoolExecutor with one thread per CPU
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        # Submit tasks to the executor
        futures = [executor.submit(check_tool_wrapper, (tool, config)) for tool, config in cli_tools.items()]

        table = PrettyTable()
        table.field_names = ["Tool", "Found Version", "Desired Version", "Compatible", "Status"]
        # Process the results as they are completed
        failed = False
        for future in concurrent.futures.as_completed(futures):
            tool, desired_version, is_available, found_version, is_compatible, is_broken = future.result()
            if is_broken:
                status = "Error on execution"
                failed = True
            elif not is_available:
                status = "Not available"
                failed = True
            else:
                status = "Available"
            if not is_compatible:
                failed = True

                # Add a row to the table
            table.add_row(
                [
                    tool,
                    found_version if found_version else "N/A",
                    desired_version,
                    "Yes" if is_compatible else "No",
                    status,
                ]
            )

        # Print the table
        print(table)
        if failed and exit_code_on_failure:
            sys.exit(1)


if __name__ == "__main__":
    report_from_pyproject_toml()
