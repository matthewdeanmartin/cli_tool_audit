"""
Wherein we learn that the package version and executable fileinfo version often don't match
because they're actually 'shimgen' shims.

Chocolatey v0.10.13: 0.10.5.0
chocolatey 0.10.13: 0.10.5.0
micro 2.0.10: 0.8.1.0
nano 2.5.3: 0.8.1.0
pandoc 2.7.3: 0.8.1.0
python 3.10.0: 3.11.1
shellcheck 0.8.0: 0.8.1.0
"""
import json
import subprocess  # nosec
from shutil import which
from typing import Any

from cli_tool_audit import check_tool_availability


def run_powershell_command(command: str) -> str:
    result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, check=True)  # nosec
    return result.stdout.strip()


def get_choco_installed_packages() -> Any:
    command = "choco list -lo  | ConvertTo-Json"
    output = run_powershell_command(command)
    return json.loads(output)


def get_file_version(executable_path: str) -> Any:
    command = f"(Get-ItemProperty '{executable_path}').VersionInfo.FileVersion"
    print(command)
    return run_powershell_command(command)


def main():
    packages = get_choco_installed_packages()
    for package in packages:
        if len(package.split(" ")) == 2 and len((package.split(" ")[1]).split(".")) == 3:
            name = package.split(" ")[0]
            # Example: Assuming package name maps directly to an executable in Program Files
            # executable_path = f"C:\\Program Files\\{package}\\{package}.exe"
            executable_path = which(name)
            if executable_path:
                version = get_file_version(executable_path)
                result = check_tool_availability(executable_path)
                print(result)
                print(f"{package}: {version}")


if __name__ == "__main__":
    main()
