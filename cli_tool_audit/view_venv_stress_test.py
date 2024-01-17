"""
Stress test for the cli_tool_audit package using venv as source data.
"""
import concurrent
import glob
import os
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# pylint: disable=no-name-in-module
from whichcraft import which

import cli_tool_audit.views as views
from cli_tool_audit.models import CliToolConfig


def get_executables_in_venv(venv_path: str) -> list[str]:
    """
    Get a list of executable commands in a Python virtual environment.

    Args:
        venv_path (str): The path to the virtual environment.

    Returns:
        list[str]: A list of executable commands in the virtual environment.
    """
    # Determine the correct directory for executables based on the OS
    if sys.platform == "win32":
        exec_dir = os.path.join(venv_path, "Scripts")
        exec_pattern = "*.exe"  # Executable pattern for Windows
    else:
        exec_dir = os.path.join(venv_path, "bin")
        exec_pattern = "*"  # In Unix-like systems, any file in bin can be an executable
    # List all executables in the directory
    executables = [os.path.basename(executable) for executable in glob.glob(os.path.join(exec_dir, exec_pattern))]

    return executables


def report_for_venv_tools(max_count: int = -1) -> None:
    """
    Report on the compatibility of the tools installed in the virtual environment.
    Args:
        max_count (int, optional): The maximum number of tools to report on. Defaults to -1.
    """
    python_path = which("python")
    venv_dir = pathlib.Path(python_path).parent.parent
    cli_tools = {}
    count = 0
    for executable in get_executables_in_venv(str(venv_dir)):
        config = CliToolConfig(executable)
        config.version_switch = "--version"
        config.version = ">=0.0.0"
        cli_tools[executable] = config
        count += 1
        if count >= max_count > 0:
            break
    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    enable_cache = len(cli_tools) >= 5
    # Create a ThreadPoolExecutor with one thread per CPU
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        # Submit tasks to the executor
        lock = Lock()
        futures = [
            executor.submit(views.check_tool_wrapper, (tool, config, lock, enable_cache))
            for tool, config in cli_tools.items()
        ]
        results = []
        # Process the results as they are completed
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
        views.pretty_print_results(results)


if __name__ == "__main__":
    report_for_venv_tools()
