import concurrent
import glob
import os
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor

from whichcraft import which

from cli_tool_audit.views import check_tool_wrapper


def get_executables_in_venv(venv_path):
    """
    Get a list of executable commands in a Python virtual environment.

    :param venv_path: Path to the virtual environment.
    :return: List of executable command names.
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


def report_for_venv_tools():
    python_path = which("python")
    venv_dir = pathlib.Path(python_path).parent.parent
    cli_tools = {}
    for executable in get_executables_in_venv(str(venv_dir)):
        cli_tools[executable] = {"version_switch": "--version", "version": ">=0.0.0"}
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
                    f"- Found Version:\n{version if version else 'N/A'}"
                    f"- Desired Version: {desired_version}"
                    f"- Compatibility: {compatible}"
                )
            else:
                print(
                    f"{tool}: {'Available' if is_available else 'Not Available'} "
                    f"- Found Version:\n{version if version else 'N/A'}"
                    f"- Desired Version: {desired_version}"
                    f"- Compatibility: {compatible}"
                )


if __name__ == "__main__":
    report_for_venv_tools()
