"""
Stress test for the cli_tool_audit package using pipx installed tools as source data.
"""

import concurrent
import json
import os
import subprocess  # nosec
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any

from tqdm import tqdm

import cli_tool_audit.call_and_compatible as call_and_compatible
import cli_tool_audit.models as models
import cli_tool_audit.views as views


#  Dummy lock for switch to ProcessPoolExecutor
class DummyLock:
    """For testing"""

    def __enter__(self):
        """For testing"""

    def __exit__(self, exc_type, exc_value, traceback):
        """For testing"""


def get_pipx_list() -> Any:
    """
    Get the output of 'pipx list --json' as a dict.

    Returns:
        Any: The output of 'pipx list --json' as a dict or None if it fails.
    """
    try:
        result = subprocess.run(
            ["pipx", "list", "--json"], shell=True, capture_output=True, text=True, check=True
        )  # nosec
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing 'pipx list --json': {e}")
        return None


def extract_apps(pipx_data: dict[str, Any]) -> dict[str, Any]:
    """
    Extract the apps from the output of 'pipx list --json'.
    Args:
        pipx_data (dict[str,Any]): The output of 'pipx list --json'.

    Returns:
        dict[str,Any]: A dictionary with the apps and their versions.
    """
    apps_dict = {}
    if pipx_data and "venvs" in pipx_data:
        for _package, data in pipx_data["venvs"].items():
            package_version = data["metadata"]["main_package"]["package_version"]
            apps = data["metadata"]["main_package"]["apps"]
            for app in apps:
                apps_dict[app] = package_version
    return apps_dict


def report_for_pipx_tools(max_count: int = -1) -> None:
    """
    Report on the compatibility of the tools installed with pipx.
    Args:
        max_count (int, optional): The maximum number of tools to report on. Defaults to -1.
    """
    pipx_data = get_pipx_list()
    apps_dict = extract_apps(pipx_data)

    # for app, version in apps_dict.items():
    #     print(f"{app}: {version}")
    count = 0
    cli_tools = {}
    for app, expected_version in apps_dict.items():
        if app in ("yated.exe", "calcure.exe", "yated", "calcure", "dedlin.exe", "dedlin"):
            # These launch interactive process & then time out.
            continue
        config = models.CliToolConfig(app)
        config.version_switch = "--version"
        config.version = f">={expected_version}"
        cli_tools[app] = config
        count += 1
        if count >= max_count > 0:
            break

    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    enable_cache = len(cli_tools) >= 5
    # Create a ThreadPoolExecutor with one thread per CPU
    lock = Lock()
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        # threaded is faster
        # lock = Dummy()
        # with ProcessPoolExecutor(max_workers=num_cpus) as executor:
        # Submit tasks to the executor
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
    report_for_pipx_tools()
