import concurrent
import json
import os
import subprocess  # nosec
from concurrent.futures import ThreadPoolExecutor

from cli_tool_audit.views import check_tool_wrapper


def get_pipx_list():
    try:
        result = subprocess.run(
            ["pipx", "list", "--json"], shell=False, capture_output=True, text=True, check=True
        )  # nosec
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing 'pipx list --json': {e}")
        return None


def extract_apps(pipx_data):
    apps_dict = {}
    if pipx_data and "venvs" in pipx_data:
        for _package, data in pipx_data["venvs"].items():
            package_version = data["metadata"]["main_package"]["package_version"]
            apps = data["metadata"]["main_package"]["apps"]
            for app in apps:
                apps_dict[app] = package_version
    return apps_dict


def report_for_pipx_tools():
    pipx_data = get_pipx_list()
    apps_dict = extract_apps(pipx_data)

    for app, version in apps_dict.items():
        print(f"{app}: {version}")

    cli_tools = {}
    for app, expected_version in apps_dict.items():
        cli_tools[app] = {"version_switch": "--version", "version": f">={expected_version}"}

    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    # Create a ThreadPoolExecutor with one thread per CPU
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        # Submit tasks to the executor
        futures = [executor.submit(check_tool_wrapper, (tool, config)) for tool, config in cli_tools.items()]

        # Process the results as they are completed
        for future in concurrent.futures.as_completed(futures):
            tool, desired_version, is_available, version, compatible, is_broken = future.result()
            if is_broken:
                pass
                # print(f"{tool}: raises errors on execution")
            elif compatible != "Compatible":
                print(
                    f"{tool}: {'Available' if is_available else 'Not Available'} "
                    f"- Version:\n{version if version else 'N/A'}, expected {apps_dict.get(tool)}"
                    f"- Compatibility: {compatible}"
                )


if __name__ == "__main__":
    report_for_pipx_tools()
