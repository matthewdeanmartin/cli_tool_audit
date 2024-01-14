import concurrent
import os
import subprocess  # nosec
from concurrent.futures import ThreadPoolExecutor

from cli_tool_audit.views import check_tool_wrapper, pretty_print_results


def list_global_npm_executables():
    # try:
    # Get the global node_modules path
    env = os.environ.copy()
    if os.name == "nt":
        cmd = "npm.cmd"
    else:
        cmd = "npm"
    out = subprocess.run([cmd, "root", "-g"], env=env, shell=False, capture_output=True, text=True, check=True)  # nosec
    node_modules_path = out.stdout.strip()

    # List the executables in the bin directory
    executables = os.listdir(node_modules_path)
    return executables
    # except subprocess.CalledProcessError as e:
    #     print(f"Error occurred: {e}")
    #     return []
    # except FileNotFoundError:
    #     print("npm is not installed or not found in PATH.")
    #     return []
    # except OSError as e:
    #     print(f"Error reading the bin directory: {e}")
    #     return []


def report_for_npm_tools() -> None:
    """
    Report on the compatibility of the tools installed with pipx.
    """
    apps = list_global_npm_executables()

    cli_tools = {}
    for app in apps:
        app_cmd = app + ".cmd"
        cli_tools[app_cmd] = {"version_switch": "--version", "version": ">=0.0.0"}

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
    report_for_npm_tools()
    # # Example usage
    # executables = list_global_npm_executables()
    # print("Global npm executables:", executables)
