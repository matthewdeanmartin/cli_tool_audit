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

from tqdm import tqdm
# pylint: disable=no-name-in-module
from whichcraft import which

import cli_tool_audit.call_and_compatible as call_and_compatible
import cli_tool_audit.models as models
import cli_tool_audit.views as views


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
        config = models.CliToolConfig(executable)
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
    # threaded is faster so far
    # with ProcessPoolExecutor(max_workers=num_cpus) as executor:
        # Submit tasks to the executor
        lock = Lock()
        # lock = Dummy()
        disable = views.should_show_progress_bar(cli_tools)
        with tqdm(total=len(cli_tools), disable=disable) as progress_bar:
            futures = [
                executor.submit(call_and_compatible.check_tool_wrapper, (tool, config, lock, enable_cache))
                for tool, config in cli_tools.items()
            ]
            results = []
            # Process the results as they are completed
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                tqdm.update(progress_bar, 1)
                results.append(result)
        print(views.pretty_print_results(results,truncate_long_versions=True, include_docs=False))


if __name__ == "__main__":
    report_for_venv_tools()
