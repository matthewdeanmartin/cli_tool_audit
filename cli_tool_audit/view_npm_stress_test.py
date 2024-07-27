"""
This module contains a stress test for the cli_tool_audit module.

It fetches all globally installed npm tools and runs them through the audit process.
"""

import concurrent
import logging
import os
import subprocess  # nosec
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from tqdm import tqdm

import cli_tool_audit.call_and_compatible as call_and_compatible
import cli_tool_audit.models as models
import cli_tool_audit.views as views

logger = logging.getLogger(__name__)


def list_global_npm_executables() -> list[str]:
    """
    List the executables in the global node_modules path.

    Returns:
        list[str]: A list of the executables in the global node_modules path.
    """
    # Get the global node_modules path
    env = os.environ.copy()
    if os.name == "nt":
        cmd = "npm.cmd"
    else:
        cmd = "npm"
    try:
        out = subprocess.run(
            [cmd, "root", "-g"], env=env, shell=True, capture_output=True, text=True, check=True
        )  # nosec
        node_modules_path = out.stdout.strip()

        # List the executables in the bin directory
        executables = os.listdir(node_modules_path)
        return executables
    except FileExistsError:
        logger.error("npm not found on path")
        return []


def report_for_npm_tools(max_count: int = -1) -> None:
    """
    Report on the compatibility of the tools installed with pipx.
    Args:
        max_count (int, optional): The maximum number of tools to report on. Defaults to -1.
    """
    apps = list_global_npm_executables()

    cli_tools = {}
    count = 0
    for app in apps:
        if os.name == "nt":
            # I think this is a windows only thing?
            app_cmd = app + ".cmd"
        else:
            app_cmd = app
        config = models.CliToolConfig(app_cmd)
        config.version_switch = "--version"
        config.version = ">=0.0.0"
        cli_tools[app_cmd] = config
        count += 1
        if 0 < count >= max_count:
            break

    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    enable_cache = len(cli_tools) >= 5
    # Create a ThreadPoolExecutor with one thread per CPU
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
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

        print(views.pretty_print_results(results, truncate_long_versions=True, include_docs=False))


if __name__ == "__main__":
    report_for_npm_tools()
