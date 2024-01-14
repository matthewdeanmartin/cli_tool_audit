"""
Stress test for the cli_tool_audit package using pipx installed tools as source data.
"""
import concurrent
import json
import os
import subprocess  # nosec
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from cli_tool_audit.views import check_tool_wrapper, pretty_print_results


def get_pipx_list() -> Any:
    """
    Get the output of 'pipx list --json' as a dict.
    """
    try:
        result = subprocess.run(
            ["pipx", "list", "--json"], shell=False, capture_output=True, text=True, check=True
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


def report_for_pipx_tools() -> None:
    """
    Report on the compatibility of the tools installed with pipx.
    """
    pipx_data = get_pipx_list()
    apps_dict = extract_apps(pipx_data)

    # for app, version in apps_dict.items():
    #     print(f"{app}: {version}")

    cli_tools = {}
    for app, expected_version in apps_dict.items():
        if app in ("yated.exe", "calcure.exe", "yated", "calcure", "dedlin.exe", "dedlin"):
            # These launch interactive process & then time out.
            continue
        cli_tools[app] = {"version_switch": "--version", "version": f">={expected_version}"}

    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    # Create a ThreadPoolExecutor with one thread per CPU
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        # Submit tasks to the executor
        futures = [executor.submit(check_tool_wrapper, (tool, config)) for tool, config in cli_tools.items()]

        results = []
        # Process the results as they are completed
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
        pretty_print_results(results)


if __name__ == "__main__":
    report_for_pipx_tools()
