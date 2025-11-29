## Tree for cli_tool_audit
```
├── .cli_tool_audit_cache/
│   ├── .gitignore
│   ├── black_b780445aca8bc5b17141b30522c5ab07.json
│   ├── choco_acb3ff132133b4cc638f6fd3018b4c06.json
│   ├── isort_9e6fb3e24115e8a8f0bb663f57bbb590.json
│   ├── make_aaf0418d3e8d542791533a3944488d8e.json
│   ├── mypy_0731164ae5719aacbaf5b9bd18660c49.json
│   ├── notepad_81c010064e5fa8c52b1d30fc89cf925a.json
│   ├── pygount_b829506909227e361210dd90697e7ade.json
│   ├── pylint_195df294ec23295b922c4011d09c6aaa.json
│   ├── python_0d9f3f4b30033fd9f79a0d9320ba927a.json
│   ├── ruff_ce4b361277f65c4e5a2085ac37c6d60e.json
│   ├── rustc_c954c6d8cb8e4f417b8451828a5ba165.json
│   └── vulture_15cb5fd387564687965ebc69ee51020a.json
├── audit_cache.py
├── audit_manager.py
├── call_and_compatible.py
├── call_tools.py
├── compatibility.py
├── compatibility_complex.py
├── config_manager.py
├── config_reader.py
├── freeze.py
├── interactive.py
├── json_utils.py
├── known_switches.py
├── logging_config.py
├── models.py
├── policy.py
├── py.typed
├── version_parsing.py
├── views.py
├── view_npm_stress_test.py
├── view_pipx_stress_test.py
├── view_venv_stress_test.py
├── __about__.py
└── __main__.py
```

## File: audit_cache.py
```python
"""
This module provides a facade for the audit manager that caches results.
"""

import datetime
import json
import logging
import pathlib
from pathlib import Path
from typing import Any

import cli_tool_audit.audit_manager as audit_manager
import cli_tool_audit.json_utils as json_utils
import cli_tool_audit.models as models

__all__ = ["AuditFacade"]


def custom_json_deserializer(data: dict[str, Any]) -> dict[str, Any]:
    """
    Custom JSON deserializer for objects not deserializable by default json code.
    Args:
        data (dict[str,Any]): The object to deserialize.

    Returns:
        dict[str,Any]: A JSON deserializable representation of the object.
    """
    if "last_modified" in data and data["last_modified"]:
        data["last_modified"] = datetime.datetime.fromisoformat(data["last_modified"])
    if "tool_config" in data and data["tool_config"]:
        for key, value in data["tool_config"].items():
            if isinstance(value, str) and key == "schema":
                data["tool_config"][key] = models.SchemaType(value)
        data["tool_config"] = models.CliToolConfig(**data["tool_config"])
    return data


logger = logging.getLogger(__name__)


class AuditFacade:
    def __init__(self, cache_dir: Path | None = None) -> None:
        """
        Initialize the facade.
        Args:
            cache_dir (Optional[str], optional): The directory to use for caching. Defaults to None.
        """
        self.audit_manager = audit_manager.AuditManager()
        self.cache_dir = cache_dir if cache_dir else Path.cwd() / ".cli_tool_audit_cache"
        self.cache_dir.mkdir(exist_ok=True)
        with open(self.cache_dir / ".gitignore", "w", encoding="utf-8") as file:
            file.write("*\n!.gitignore\n")

        self.clear_old_cache_files()
        self.cache_hit = False

    def clear_old_cache_files(self) -> None:
        """
        Clear cache files that are older than 30 days.
        """
        current_time = datetime.datetime.now()
        expiration_days = 30
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                file_creation_time = datetime.datetime.fromtimestamp(cache_file.stat().st_mtime)
                if (current_time - file_creation_time) > datetime.timedelta(days=expiration_days):
                    if cache_file.exists():
                        cache_file.unlink(missing_ok=True)  # Delete the file
            except FileNotFoundError:
                # This appears to be intermittent. If it is already gone, no problem, I guess.
                logger.debug(f"Failed to find cache file {cache_file}")

    def get_cache_filename(self, tool_config: models.CliToolConfig) -> Path:
        """
        Get the cache filename for the given tool.
        Args:
            tool_config (models.CliToolConfig): The tool to get the cache filename for.

        Returns:
            Path: The cache filename.
        """
        sanitized_name = tool_config.name.replace(".", "_")
        the_hash = tool_config.cache_hash()
        return self.cache_dir / f"{sanitized_name}_{the_hash}.json"

    def read_from_cache(self, tool_config: models.CliToolConfig) -> models.ToolCheckResult | None:
        """
        Read the cached result for the given tool.
        Args:
            tool_config (models.CliToolConfig): The tool to get the cached result for.

        Returns:
            Optional[models.ToolCheckResult]: The cached result or None if not found.
        """
        cache_file = self.get_cache_filename(tool_config)
        if cache_file.exists():
            logger.debug(f"Cache hit for {tool_config.name}")
            try:
                with open(cache_file, encoding="utf-8") as file:
                    hit = models.ToolCheckResult(**json.load(file, object_hook=custom_json_deserializer))
                    self.cache_hit = True
                    return hit
            except TypeError:
                pathlib.Path(cache_file).unlink()
                self.cache_hit = False
                return None
        logger.debug(f"Cache miss for {tool_config.name}")
        self.cache_hit = False
        return None

    def write_to_cache(self, tool_config: models.CliToolConfig, result: models.ToolCheckResult) -> None:
        """
        Write the given result to the cache.
        Args:
            tool_config (models.CliToolConfig): The tool to write the result for.
            result (models.ToolCheckResult): The result to write.
        """
        cache_file = self.get_cache_filename(tool_config)
        with open(cache_file, "w", encoding="utf-8") as file:
            logger.debug(f"Caching {tool_config.name}")
            json.dump(result.__dict__, file, ensure_ascii=False, indent=4, default=json_utils.custom_json_serializer)

    def call_and_check(self, tool_config: models.CliToolConfig) -> models.ToolCheckResult:
        """
        Call and check the given tool.
        Args:
            tool_config (models.CliToolConfig): The tool to call and check.

        Returns:
            models.ToolCheckResult: The result of the check.
        """
        cached_result = self.read_from_cache(tool_config)
        if cached_result:
            return cached_result

        result = self.audit_manager.call_and_check(tool_config)
        if not result.is_problem():
            # Don't cache problems. Assume user will fix it soon.
            self.write_to_cache(tool_config, result)
        return result
```
## File: audit_manager.py
```python
"""
Class to audit a tool, abstract base class to allow for supporting different version schemas.

Includes several implementations of VersionChecker, which are used by AuditManager.
"""

import datetime
import logging
import os
import subprocess  # nosec
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

import packaging.specifiers as packaging_specifiers
import packaging.version as packaging
from semver import Version
from whichcraft import which

import cli_tool_audit.compatibility as compatibility
import cli_tool_audit.models as models
import cli_tool_audit.version_parsing as version_parsing
from cli_tool_audit.known_switches import KNOWN_SWITCHES

ExistenceVersionStatus = Literal["Found", "Not Found"]

logger = logging.getLogger(__name__)


@dataclass
class VersionResult:
    is_compatible: bool
    clean_format: str


class VersionChecker(ABC):
    """
    Abstract base class for checking if a version is compatible with a desired version.
    """

    @abstractmethod
    def check_compatibility(self, desired_version: str) -> VersionResult:
        """
        Check if the version is compatible with the desired version.
        Args:
            desired_version (str): The desired version.

        Returns:
            VersionResult: The result of the check.
        """

    @abstractmethod
    def format_report(self, desired_version: str) -> str:
        """
        Format a report on the compatibility of a version with a desired version.
        Args:
            desired_version (str): The desired version.

        Returns:
            str: The formatted report.
        """


class SemVerChecker(VersionChecker):
    def __init__(self, version_string: str) -> None:
        self.found_version = self.parse_version(version_string)
        self.result: VersionResult | None = None

    def parse_version(self, version_string: str) -> Version | None:
        """
        Parse a version string into a semver Version object.
        Args:
            version_string (str): The version string to parse.

        Returns:
            Optional[Version]: The parsed version or None if the version string is invalid.
        """
        return version_parsing.two_pass_semver_parse(version_string)

    def check_compatibility(self, desired_version: str | None) -> VersionResult:
        """
        Check if the version is compatible with the desired version.
        Args:
            desired_version (Optional[str]): The desired version.

        Returns:
            VersionResult: The result of the check.
        """
        if not self.found_version:
            return VersionResult(is_compatible=False, clean_format="Invalid Format")
        desired_version = desired_version or "0.0.0"
        compatible_result, _version_object = compatibility.check_compatibility(desired_version, str(self.found_version))

        self.result = VersionResult(
            is_compatible=compatible_result == "Compatible", clean_format=str(self.found_version)
        )
        return self.result

    def format_report(self, desired_version: str) -> str:
        """
        Format a report on the compatibility of a version with a desired version.
        Args:
            desired_version (str): The desired version.

        Returns:
            str: The formatted report.
        """
        if not self.found_version or not self.result:
            return "Invalid Format"
        return "Compatible" if self.result.is_compatible else f"{self.found_version} != {desired_version}"


class ExistenceVersionChecker(VersionChecker):
    def __init__(self, version_string: ExistenceVersionStatus) -> None:
        """
        Check if a tool exists.
        Args:
            version_string (str): A constant, "Found" or "Not Found"
        """
        if version_string not in ("Found", "Not Found"):
            raise ValueError(f"version_string must be 'Found' or 'Not Found', not {version_string}")
        self.found_version = version_string

    def check_compatibility(self, desired_version: str) -> VersionResult:
        """
        Check if the tool exists.
        Args:
            desired_version (strshould_show_progress_bar): The desired version. Ignored.

        Returns:
            VersionResult: The result of the check.
        """
        return VersionResult(is_compatible=self.found_version == desired_version, clean_format=self.found_version)

    def format_report(self, desired_version: str) -> str:
        """
        Format a report on the compatibility of a version with a desired version.
        Args:
            desired_version (str): The desired version.

        Returns:
            str: The formatted report.
        """
        return "Compatible" if self.found_version == desired_version else "Not Found"


class SnapshotVersionChecker(VersionChecker):
    """
    Check if a version is compatible with a desired version using snapshot versioning.

    Snapshot versioning is where the entire string returned by `cmd --version` represents
    the version and the version string has no internal structure, no ordering and no
    possibility of version range checking.
    """

    def __init__(self, version_string: str) -> None:
        """
        Check if a version is compatible with a desired version using snapshot versioning.
        """
        self.found_version = self.parse_version(version_string)

    def parse_version(self, version_string: str) -> str:
        """
        A no-op, the version string is already parsed.

        Args:
            version_string (str): The version string to parse.

        Returns:
            str: The unchanged version.
        """
        return version_string

    def check_compatibility(self, desired_version: str | None) -> VersionResult:
        """
        Check if the version is compatible with the desired version which could be a range.
        Args:
            desired_version (Optional[str]): The desired version.

        Returns:
            VersionResult: The result of the check.
        """
        return VersionResult(is_compatible=self.found_version == desired_version, clean_format=self.found_version)

    def format_report(self, desired_version: str) -> str:
        """
        Format a report on the compatibility of a version with a desired version.
        Args:
            desired_version (str): The desired version.

        Returns:
            str: The formatted report.
        """
        return "Compatible" if self.found_version == desired_version else "different"


class Pep440VersionChecker(VersionChecker):
    """
    Check if a version is compatible with a desired version using PEP 440 versioning.
    """

    def __init__(self, version_string: str) -> None:
        """
        Check if a version is compatible with a desired version using PEP 440 versioning.
        Args:
            version_string (str): The version string to check.
        """
        self.found_version = self.parse_version(version_string)

    def parse_version(self, version_string: str) -> packaging.Version:
        """
        Parse a version string into a packaging.Version object.
        Args:
            version_string (str): The version string to parse.

        Returns:
            packaging.Version: The parsed version.
        """
        return packaging.Version(version_string)

    def check_compatibility(self, desired_version: str | None) -> VersionResult:
        """
        Check if the version is compatible with the desired version which could be a range.

        Args:
            desired_version (Optional[str]): The desired version.

        Returns:
            VersionResult: The result of the check.
        """
        # Range match
        if not desired_version:
            # Treat blank as "*"
            return VersionResult(is_compatible=True, clean_format=str(self.found_version))
        if " " in desired_version or ">" in desired_version or "<" in desired_version or "~" in desired_version:
            specifier = packaging_specifiers.SpecifierSet(desired_version)
            return VersionResult(
                is_compatible=specifier.contains(self.found_version), clean_format=str(self.found_version)
            )
        # exact match
        return VersionResult(
            is_compatible=self.found_version == packaging.Version(desired_version), clean_format=str(self.found_version)
        )

    def format_report(self, desired_version: str) -> str:
        """
        Format a report on the compatibility of a version with a desired version.
        Args:
            desired_version (str): The desired version.

        Returns:
            str: The formatted report.
        """
        return "Compatible" if self.found_version == desired_version else f"{self.found_version} != {desired_version}"


class AuditManager:
    """
    Class to audit a tool, abstract base class to allow for supporting different version schemas.
    """

    def call_and_check(self, tool_config: models.CliToolConfig) -> models.ToolCheckResult:
        """
        Call and check the given tool.
        Args:
            tool_config (models.CliToolConfig): The tool to call and check.

        Returns:
            models.ToolCheckResult: The result of the check.
        """
        tool, config = tool_config.name, tool_config

        if config.if_os and not sys.platform.startswith(config.if_os):
            # This isn't very transparent about what just happened
            logger.debug(f"Skipping {tool} because it's not needed for {sys.platform}")
            return models.ToolCheckResult(
                tool=tool,
                is_needed_for_os=False,
                desired_version=config.version or "0.0.0",
                is_available=False,
                found_version=None,
                parsed_version=None,
                is_snapshot=False,
                is_compatible=f"{sys.platform}, not {config.if_os}",
                is_broken=False,
                last_modified=None,
                tool_config=config,
            )
        result = self.call_tool(
            tool,
            config.schema or models.SchemaType.SEMVER,
            config.version_switch or "--version",
        )

        # Not pretty.
        if config.schema == models.SchemaType.EXISTENCE:
            logger.debug(f"Checking {tool} for existence only.")
            existence_checker = ExistenceVersionChecker("Found" if result.is_available else "Not Found")
            version_result = existence_checker.check_compatibility("Found")
            compatibility_report = existence_checker.format_report("Found")
            desired_version = "*"
        elif config.schema == models.SchemaType.SNAPSHOT:
            logger.debug(f"Checking {tool} for snapshot versioning.")
            snapshot_checker = SnapshotVersionChecker(result.version or "")
            version_result = snapshot_checker.check_compatibility(config.version)
            compatibility_report = snapshot_checker.format_report(config.version or "")
            desired_version = config.version or ""
        elif config.schema == "pep440":
            logger.debug(f"Checking {tool} for PEP 440 versioning.")
            pep440_checker = Pep440VersionChecker(result.version or "")
            version_result = pep440_checker.check_compatibility(config.version or "0.0.0")
            compatibility_report = pep440_checker.format_report(config.version or "0.0.0")
            desired_version = config.version or "*"
        else:  # config.schema == "semver":
            logger.debug(f"Checking {tool} for semantic versioning.")
            semver_checker = SemVerChecker(result.version or "")

            # Have to clean up desired semver or semver will blow up on bad input.

            if config.version != "*":
                symbols, desired_version_text = compatibility.split_version_match_pattern(config.version or "")
                desired_version_text = str(version_parsing.two_pass_semver_parse(desired_version_text or ""))
                if symbols:
                    clean_desired_semver = f"{symbols}{desired_version_text}"
                else:
                    clean_desired_semver = desired_version_text
            else:
                clean_desired_semver = "*"
            logger.debug(f"Ready to semver_check with {clean_desired_semver}")
            version_result = semver_checker.check_compatibility(clean_desired_semver)
            compatibility_report = semver_checker.format_report(config.version or "0.0.0")
            desired_version = config.version or "*"

        return models.ToolCheckResult(
            tool=tool,
            desired_version=desired_version,
            is_needed_for_os=True,
            is_available=result.is_available,
            is_snapshot=bool(config.schema == models.SchemaType.SNAPSHOT),
            found_version=result.version,
            parsed_version=version_result.clean_format,
            is_compatible=compatibility_report,
            is_broken=result.is_broken,
            last_modified=result.last_modified,
            tool_config=config,
        )

    def call_tool(
        self,
        tool_name: str,
        schema: models.SchemaType,
        version_switch: str = "--version",
    ) -> models.ToolAvailabilityResult:
        """
        Check if a tool is available in the system's PATH and if possible, determine a version number.

        Args:
            tool_name (str): The name of the tool to check.
            schema (SchemaType): The version schema to use.
            version_switch (str): The switch to get the tool version. Defaults to '--version'.


        Returns:
            ToolAvailabilityResult: An object containing the availability and version of the tool.
        """
        # Check if the tool is in the system's PATH
        is_broken = True

        last_modified = self.get_command_last_modified_date(tool_name)
        if not last_modified:
            logger.warning(f"{tool_name} is not on path, no last modified.")
            return models.ToolAvailabilityResult(False, True, None, last_modified)
        if schema == models.SchemaType.EXISTENCE:
            logger.debug(f"{tool_name} exists, but not checking for version.")
            return models.ToolAvailabilityResult(True, False, None, last_modified)

        if version_switch is None or version_switch == "--version":
            # override default.
            # Could be a problem if KNOWN_SWITCHES was ever wrong.
            version_switch = KNOWN_SWITCHES.get(tool_name, "--version")

        version = None

        # pylint: disable=broad-exception-caught
        try:
            command = [tool_name, version_switch]
            timeout = int(os.environ.get("CLI_TOOL_AUDIT_TIMEOUT", 15))
            use_shell = bool(os.environ.get("CLI_TOOL_AUDIT_USE_SHELL", False))
            if not use_shell:
                logger.debug(
                    "Some tools like pipx, may not be found on the path unless you export "
                    "CLI_TOOL_AUDIT_USE_SHELL=1. By default tools are checked without a shell for security."
                )
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, shell=use_shell, check=True
            )  # nosec
            # Sometimes version is on line 2 or later.
            version = result.stdout.strip()
            if not version:
                # check stderror
                logger.debug("Got nothing from stdout, checking stderror")
                version = result.stderr.strip()

            logger.debug(f"Called tool with {' '.join(command)}, got  {version}")
            is_broken = False
        except subprocess.CalledProcessError as exception:
            is_broken = True
            logger.error(f"{tool_name} failed invocation with {exception}")
            logger.error(f"{tool_name} stderr: {exception.stderr}")
            logger.error(f"{tool_name} stdout: {exception.stdout}")
        except FileNotFoundError:
            logger.error(f"{tool_name} is not on path, file not found.")
            return models.ToolAvailabilityResult(False, True, None, last_modified)

        return models.ToolAvailabilityResult(True, is_broken, version, last_modified)

    def get_command_last_modified_date(self, tool_name: str) -> datetime.datetime | None:
        """
        Get the last modified date of a command's executable.
        Args:
            tool_name (str): The name of the command.

        Returns:
            Optional[datetime.datetime]: The last modified date of the command's executable.
        """
        # Find the path of the command's executable
        result = which(tool_name)
        if result is None:
            return None

        executable_path = result

        # Get the last modified time of the executable
        last_modified_timestamp = os.path.getmtime(executable_path)
        return datetime.datetime.fromtimestamp(last_modified_timestamp)
```
## File: call_and_compatible.py
```python
"""
Merge tool call and compatibility check results.
"""

import logging
import sys
import threading

import cli_tool_audit.audit_cache as audit_cache
import cli_tool_audit.audit_manager as audit_manager
import cli_tool_audit.models as models

logger = logging.getLogger(__name__)


def check_tool_wrapper(
    tool_info: tuple[str, models.CliToolConfig, threading.Lock, bool],
) -> models.ToolCheckResult:
    """
    Wrapper function for check_tool_availability() that returns a ToolCheckResult object.

    Args:
        tool_info (tuple[str, models.CliToolConfig, threading.Lock, bool]): A tuple containing the tool name, the
        CliToolConfig object, a lock, and a boolean indicating if the cache is enabled.

    Returns:
        models.ToolCheckResult: A ToolCheckResult object.
    """
    tool, config, lock, enable_cache = tool_info

    if config.if_os and not sys.platform.startswith(config.if_os):
        # This isn't very transparent about what just happened
        logger.debug(f"Skipping {tool} because it's not needed for {sys.platform}")
        return models.ToolCheckResult(
            is_needed_for_os=False,
            tool=tool,
            desired_version=config.version or "0.0.0",
            is_available=False,
            found_version=None,
            parsed_version=None,
            is_snapshot=False,
            is_compatible=f"{sys.platform}, not {config.if_os}",
            is_broken=False,
            last_modified=None,
            tool_config=config,
        )

    config.name = tool
    config.version_switch = config.version_switch or "--version"

    if enable_cache:
        cached_manager = audit_cache.AuditFacade()
        with lock:
            logger.debug(f"Checking {tool} with cache")
            return cached_manager.call_and_check(tool_config=config)

    manager = audit_manager.AuditManager()
    return manager.call_and_check(tool_config=config)
```
## File: call_tools.py
```python
"""
Check if an external tool is expected and available on the PATH.

Also, check version.

Possible things that could happen
- found/not found on path
- found but can't run without error
- found, runs but wrong version switch
- found, has version but cli version != package version
"""

import datetime
import logging
import os
import subprocess  # nosec

# pylint: disable=no-name-in-module
from whichcraft import which

import cli_tool_audit.models as models
from cli_tool_audit.known_switches import KNOWN_SWITCHES

logger = logging.getLogger(__name__)


def get_command_last_modified_date(tool_name: str) -> datetime.datetime | None:
    """
    Get the last modified date of a command's executable.
    Args:
        tool_name (str): The name of the command.

    Returns:
        Optional[datetime.datetime]: The last modified date of the command's executable.
    """
    # Find the path of the command's executable
    result = which(str(tool_name))
    if result is None:
        return None

    executable_path = result

    # Get the last modified time of the executable
    last_modified_timestamp = os.path.getmtime(executable_path)
    return datetime.datetime.fromtimestamp(last_modified_timestamp)


def check_tool_availability(
    tool_name: str,
    schema: models.SchemaType,
    version_switch: str = "--version",
) -> models.ToolAvailabilityResult:
    """
    Check if a tool is available in the system's PATH and if possible, determine a version number.

    Args:
        tool_name (str): The name of the tool to check.
        schema (models.SchemaType): The schema to use for the version.
        version_switch (str): The switch to get the tool version. Defaults to '--version'.


    Returns:
        models.ToolAvailabilityResult: An object containing the availability and version of the tool.
    """
    # Check if the tool is in the system's PATH
    is_broken = True

    last_modified = get_command_last_modified_date(tool_name)
    if not last_modified:
        logger.warning(f"{tool_name} is not on path, no last modified.")
        return models.ToolAvailabilityResult(False, True, None, last_modified)
    if schema == models.SchemaType.EXISTENCE:
        logger.debug(f"{tool_name} exists, but not checking for version.")
        return models.ToolAvailabilityResult(True, False, None, last_modified)

    if version_switch is None or version_switch == "--version":
        # override default.
        # Could be a problem if KNOWN_SWITCHES was ever wrong.
        version_switch = KNOWN_SWITCHES.get(tool_name, "--version")

    version = None

    # pylint: disable=broad-exception-caught
    try:
        command = [tool_name, version_switch]
        timeout = int(os.environ.get("CLI_TOOL_AUDIT_TIMEOUT", 15))
        use_shell = bool(os.environ.get("CLI_TOOL_AUDIT_USE_SHELL", False))
        if not use_shell:
            logger.debug(
                "Some tools like pipx, may not be found on the path unless you export "
                "CLI_TOOL_AUDIT_USE_SHELL=1. By default tools are checked without a shell for security."
            )
        logger.info(f"Checking {tool_name} with {' '.join(command)}")
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, shell=use_shell, check=True
        )  # nosec
        # Sometimes version is on line 2 or later.
        version = result.stdout.strip()
        if not version:
            # check stderror
            logger.debug("Got nothing from stdout, checking stderror")
            version = result.stderr.strip()

        logger.debug(f"Called tool with {' '.join(command)}, got  {version}")
        is_broken = False
    except subprocess.CalledProcessError as exception:
        is_broken = True
        logger.error(f"{tool_name} failed invocation with {exception}")
        logger.error(f"{tool_name} stderr: {exception.stderr}")
        logger.error(f"{tool_name} stdout: {exception.stdout}")
    except FileNotFoundError:
        logger.error(f"{tool_name} is not on path, file not found.")
        return models.ToolAvailabilityResult(False, True, None, last_modified)

    return models.ToolAvailabilityResult(True, is_broken, version, last_modified)


if __name__ == "__main__":
    print(get_command_last_modified_date("asdfpipx"))
```
## File: compatibility.py
```python
"""
Functions for checking compatibility between versions.
"""

import logging
import re
from typing import Any

from semver import Version

import cli_tool_audit.compatibility_complex as compatibility_complex
import cli_tool_audit.version_parsing as version_parsing

logger = logging.getLogger(__name__)


def split_version_match_pattern(pattern: str) -> tuple[Any, ...]:
    """
    Split a version match pattern into a comparator and a version number.

    Args:
        pattern (str): The version match pattern.

    Returns:
        Tuple[Optional[str],Optional[str]]: A tuple with the first element being the comparator and the second element
            being the version number.

    Examples:
        >>> split_version_match_pattern(">=1.1.1")
        ('>=', '1.1.1')
        >>> split_version_match_pattern("1.1.1")
        ('', '1.1.1')
        >>> split_version_match_pattern("==1.1.1")
        ('==', '1.1.1')
        >>> split_version_match_pattern("~=1.1.1")
        ('~=', '1.1.1')
        >>> split_version_match_pattern("!=1.1.1")
        ('!=', '1.1.1')
        >>> split_version_match_pattern("<=1.1.1")
        ('<=', '1.1.1')
        >>> split_version_match_pattern("<1.1.1")
        ('<', '1.1.1')
        >>> split_version_match_pattern(">1.1.1")
        ('>', '1.1.1')
    """
    # Regular expression for version match pattern
    match_pattern_regex = r"(>=|<=|!=|>|<|==|~=|~|^)?(.*)"

    # Search for the pattern
    match = re.match(match_pattern_regex, pattern)

    # Return the comparator and version number if match is found
    if match:
        return match.groups()
    return None, None


CANT_TELL = "Can't tell"


def check_compatibility(desired_version: str, found_version: str | None) -> tuple[str, Version | None]:
    """
    Check if a found version is compatible with a desired version. Uses semantic versioning.
    When a version isn't semver, we attempt to convert it to semver.

    Args:
        desired_version (str): The desired version.
        found_version (str): The found version.

    Returns:
        str: A string indicating if the versions are compatible or not.
        Version: The parsed version if found.

    Examples:
        >>> check_compatibility(">=1.1.1", "1.1.1")
        ('Compatible', Version(major=1, minor=1, patch=1, prerelease=None, build=None))
        >>> check_compatibility(">=1.1.1", "1.1.0")
        ('>=1.1.1 != 1.1.0', Version(major=1, minor=1, patch=0, prerelease=None, build=None))
        >>> check_compatibility(">=1.1.1", "1.1.2")
        ('Compatible', Version(major=1, minor=1, patch=2, prerelease=None, build=None))
    """
    if desired_version == "*":
        return "Compatible", None
    if not found_version:
        logger.info(f"Tool provided no versions, so can't tell. {desired_version}/{found_version}")
        return CANT_TELL, None

    # desired is a match expression, e.g. >=1.1.1

    # Handle non-semver match patterns
    symbols, desired_version_text = split_version_match_pattern(desired_version)
    logger.debug(f"Attempted to split {desired_version} and got {symbols} and {desired_version_text}")
    clean_desired_version = None
    try:
        logger.debug("1st check with two_pass_semver_parse")
        clean_desired_version = version_parsing.two_pass_semver_parse(desired_version_text)
        logger.debug(f"clean_desired_version: {clean_desired_version} for {desired_version_text}")
    except ValueError:
        logger.warning("Can't parse desired version as semver")

    if clean_desired_version:
        desired_version = f"{symbols}{clean_desired_version}"

    found_semversion = None
    try:
        logger.debug("2nd check with two_pass_semver_parse")
        found_semversion = version_parsing.two_pass_semver_parse(found_version)
        logger.debug(f"found_semversion: {found_semversion} for {found_version}")
        logger.debug(f"desired_version: {desired_version}")
        if found_semversion is None:
            logger.warning(f"SemVer failed to parse {desired_version}/{found_version}")
            is_compatible = CANT_TELL
        elif desired_version == "*":
            # not picky, short circuit the logic.
            is_compatible = "Compatible"
        elif (
            desired_version.startswith("^")
            or desired_version.startswith("~")
            or "*" in desired_version
            or desired_version.startswith("=")
            or desired_version.startswith("!")
            or desired_version.startswith("<")
            or desired_version.startswith(">")
        ):
            is_compatible = compatibility_complex.check_range_compatibility(desired_version, found_semversion)
        elif found_semversion.match(desired_version):
            is_compatible = "Compatible"
        else:
            is_compatible = f"{desired_version} != {found_semversion}"
    except ValueError as value_error:
        logger.warning(f"Can't tell {desired_version}/{found_version}: {value_error}")
        is_compatible = CANT_TELL
    except TypeError as type_error:
        logger.warning(f"Can't tell {desired_version}/{found_version}: {type_error}")
        is_compatible = CANT_TELL
    return is_compatible, found_semversion


if __name__ == "__main__":
    print(check_compatibility("^1.0.0", "8.2.3"))
```
## File: compatibility_complex.py
```python
"""
This module contains functions to check if a found version is compatible with a desired version range.
"""

from packaging.version import parse
from semver import Version


def convert_version_range(version_range: str) -> str:
    """
    Convert a version range to a range that can be used with semantic versioning.

    Args:
        version_range (str): The version range.

    Returns:
        str: The converted version range.

    Examples:
        >>> convert_version_range("^1.2.3")
        '>=1.2.3 <2.0.0'
        >>> convert_version_range("~1.2")
        '>=1.2 <1.3.0'
    """
    if not version_range.startswith(("^", "~")) and "*" not in version_range:
        raise ValueError("Version range must start with ^ or ~")

    if "*" in version_range:
        parts = version_range.split(".")
        if version_range == "*":
            return ">=0.0.0"
        if len(parts) == 2 and parts[1] == "*":  # e.g., 1.*
            major = parts[0]
            return f">={major}.0.0 <{int(major) + 1}.0.0"
        if len(parts) == 3 and parts[2] == "*":  # e.g., 1.2.*
            major, minor = parts[:2]
            return f">={major}.{minor}.0 <{major}.{int(minor) + 1}.0"

    operator = version_range[0]
    version = parse(version_range[1:])

    if operator == "^":
        if version.major != 0 or (version.major == 0 and version.minor == 0):
            return f">={version} <{version.major + 1}.0.0"
        if version.minor != 0:
            return f">={version} <{version.major}.{version.minor + 1}.0"
        return f">={version} <{version.major}.{version.minor}.{version.micro + 1}"

    if operator == "~":
        if version.minor is not None and version.micro is not None:
            return f">={version} <{version.major}.{version.minor + 1}.0"
        if version.minor is None:
            return f">={version.major}.0.0 <{version.major + 1}.0.0"
    raise ValueError("Version range must start with ^ or ~ or contain *")


def check_range_compatibility(desired_version: str, found_semversion: Version) -> str:
    """
    Check if a found version is compatible with a desired version range.

    Args:
        desired_version (str): The desired version range.
        found_semversion (Version): The found version.

    Returns:
        str: A string indicating if the versions are compatible or not.

    Examples:
        >>> check_range_compatibility("^1.1.1", Version.parse("1.1.1"))
        'Compatible'
        >>> check_range_compatibility("^1.1.1", Version.parse("1.1.0"))
        '^1.1.1 != 1.1.0'
        >>> check_range_compatibility("~1.2.0", Version.parse("1.2.5"))
        'Compatible'
    """
    if desired_version == "*":
        return "Compatible"
    if (
        desired_version.startswith("=")
        or desired_version.startswith("!")
        or desired_version.startswith("<")
        or desired_version.startswith(">")
    ):
        version_string = desired_version
    else:
        version_string = convert_version_range(desired_version)

    parts = version_string.split(" ")
    if len(parts) == 1:
        if not found_semversion.match(parts[0]):
            return f"{desired_version} != {found_semversion}"
        return "Compatible"

    lower, upper = parts
    if not found_semversion.match(lower):
        return f"{desired_version} != {found_semversion}"
    if not found_semversion.match(upper):
        return f"{desired_version} != {found_semversion}"
    return "Compatible"


if __name__ == "__main__":
    # Example Usage
    print(check_range_compatibility("~1.0.0", Version(8, 32, 0)))
    print(convert_version_range("^1.2.3"))  # Output: >=1.2.3 <2.0.0
    print(convert_version_range("~1.2"))  # Output: >=1.2.0 <1.3.0
```
## File: config_manager.py
```python
import copy
import os
from pathlib import Path
from typing import Any, cast

import toml
import tomlkit

import cli_tool_audit.models as models


class ConfigManager:
    """
    Manage the config file.
    """

    def __init__(self, config_path: Path) -> None:
        """
        Args:
            config_path (Path): The path to the toml file.
        """
        self.config_path = config_path
        self.tools: dict[str, models.CliToolConfig] = {}

    def read_config(self) -> bool:
        """
        Read the cli-tools section from a toml file.

        Returns:
            bool: True if the cli-tools section exists, False otherwise.
        """
        if self.config_path.exists():
            with open(str(self.config_path), encoding="utf-8") as file:
                # okay this is too hard.
                # from tomlkit.items import Item
                # class SchemaTypeItem(Item):
                #     def __init__(self, value:SchemaType):
                #         self.value = value
                #     def as_string(self):
                #         return str(self.value)
                #
                # def encoder(value):
                #     if isinstance(value, SchemaType):
                #         return SchemaTypeItem(value.value)
                #     raise TypeError(f"Unknown type {type(value)}")
                # tomlkit.register_encoder(lambda x: x.value)
                # TODO: switch to tomkit and clone the config/settings
                # so that we can use it like ordinary python
                config = toml.load(file)
                tools_config = config.get("tool", {}).get("cli-tools", {})
                for tool_name, settings in tools_config.items():
                    if settings.get("only_check_existence"):
                        settings["schema"] = models.SchemaType.EXISTENCE
                        del settings["only_check_existence"]
                    elif settings.get("version_snapshot"):
                        settings["schema"] = models.SchemaType.SNAPSHOT
                        settings["version"] = settings.get("version_snapshot")
                        del settings["version_snapshot"]

                    settings["name"] = tool_name
                    if settings.get("schema"):
                        settings["schema"] = models.SchemaType(str(settings["schema"]).lower())
                    else:
                        settings["schema"] = models.SchemaType.SEMVER
                    self.tools[tool_name] = models.CliToolConfig(**settings)
        return bool(self.tools)

    def create_tool_config(self, tool_name: str, config: dict) -> None:
        """
        Create a new tool config.

        Args:
            tool_name (str): The name of the tool.
            config (dict): The config for the tool.

        Raises:
            ValueError: If the tool already exists.
        """
        if not self.tools:
            self.read_config()
        if tool_name in self.tools:
            raise ValueError(f"Tool {tool_name} already exists")
        config["name"] = tool_name
        self.tools[tool_name] = models.CliToolConfig(**config)
        self._save_config()

    def update_tool_config(self, tool_name: str, config: dict) -> None:
        """
        Update an existing tool config.
        Args:
            tool_name (str): The name of the tool.
            config (dict): The config for the tool.

        Raises:
            ValueError: If the tool does not exist.
        """
        if not self.tools:
            self.read_config()
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} does not exist")
        for key, value in config.items():
            setattr(self.tools[tool_name], key, value)
        self._save_config()

    def create_update_tool_config(self, tool_name: str, config: dict) -> None:
        """
        Create or update a tool config.
        Args:
            tool_name (str): The name of the tool.
            config (dict): The config for the tool.
        """
        if not self.tools:
            self.read_config()
        if tool_name not in self.tools:
            config["name"] = tool_name
            self.tools[tool_name] = models.CliToolConfig(**config)
        else:
            for key, value in config.items():
                if key == "schema":
                    value = str(models.SchemaType(value))
                setattr(self.tools[tool_name], key, value)
        self._save_config()

    def delete_tool_config(self, tool_name: str) -> None:
        """
        Delete an existing tool config.
        Args:
            tool_name (str): The name of the tool.
        """
        if not self.tools:
            self.read_config()
        if tool_name not in self.tools:
            return
        del self.tools[tool_name]
        self._save_config()

    def _save_config(self) -> None:
        """
        Save the config to the file.
        """
        # Read the entire existing config
        if os.path.exists(self.config_path):
            with open(self.config_path, encoding="utf-8") as file:
                config = tomlkit.parse(file.read())
        else:
            config = tomlkit.document()

        # Access or create the 'cli-tools' section
        if "tool" not in config:
            config["tool"] = tomlkit.table()
        if "cli-tools" not in cast(Any, config.get("tool")):
            cast(Any, config["tool"])["cli-tools"] = tomlkit.table()

        # Update the 'cli-tools' section with inline tables
        for tool_name, tool_config in self.tools.items():
            inline_table = tomlkit.inline_table()
            for key, value in vars(tool_config).items():
                if value is not None:
                    # TODO: could use custom toml encoder here?
                    if key == "schema":
                        value = str(value)
                    inline_table[key] = value
            cast(Any, cast(Any, config["tool"])["cli-tools"])[tool_name] = inline_table

        # Handle deletes
        for tool in copy.deepcopy(cast(Any, cast(Any, config["tool"])["cli-tools"])):
            if tool not in self.tools:
                del cast(Any, cast(Any, config["tool"])["cli-tools"])[tool]

        # Write the entire config back to the file
        with open(self.config_path, "w", encoding="utf-8") as file:
            file.write(tomlkit.dumps(config))


if __name__ == "__main__":
    # Usage example
    def run() -> None:
        """Example"""
        config_manager = ConfigManager(Path("../pyproject.toml"))
        c = config_manager.read_config()
        print(c)

    run()
```
## File: config_reader.py
```python
"""
Read list of tools from config.
"""

import logging
from pathlib import Path

import cli_tool_audit.config_manager as config_manager
import cli_tool_audit.models as models

logger = logging.getLogger(__name__)


def read_config(file_path: Path) -> dict[str, models.CliToolConfig]:
    """
    Read the cli-tools section from a pyproject.toml file.

    Args:
        file_path (Path): The path to the pyproject.toml file.

    Returns:
        dict[str, models.CliToolConfig]: A dictionary with the cli-tools section.
    """
    # pylint: disable=broad-exception-caught
    try:
        logger.debug(f"Loading config from {file_path}")
        manager = config_manager.ConfigManager(file_path)
        found = manager.read_config()
        if not found:
            logger.warning("Config section not found, expected [tool.cli-tools] with values")
        return manager.tools
    except BaseException as e:
        logger.error(e)
        print(f"Error reading pyproject.toml: {e}")
        return {}
```
## File: freeze.py
```python
"""
Capture current version of a list of tools.
"""

import os
import tempfile
from pathlib import Path

import cli_tool_audit.call_tools as call_tools
import cli_tool_audit.config_manager as cm
import cli_tool_audit.models as models


def freeze_requirements(tool_names: list[str], schema: models.SchemaType) -> dict[str, models.ToolAvailabilityResult]:
    """
    Capture the current version of a list of tools.

    Args:
        tool_names (list[str]): A list of tool names.
        schema (SchemaType): The schema to use for the version.

    Returns:
        dict[str, call_tools.ToolAvailabilityResult]: A dictionary of tool names and versions.
    """
    results = {}
    for tool_name in tool_names:
        result = call_tools.check_tool_availability(tool_name, schema, "--version")
        results[tool_name] = result
    return results


def freeze_to_config(tool_names: list[str], config_path: Path, schema: models.SchemaType) -> None:
    """
    Capture the current version of a list of tools and write them to a config file.

    Args:
        tool_names (list[str]): A list of tool names.
        config_path (Path): The path to the config file.
        schema (SchemaType): The schema to use for the version.
    """
    results = freeze_requirements(tool_names, schema=schema)
    config_manager = cm.ConfigManager(config_path)
    config_manager.read_config()
    for tool_name, result in results.items():
        if result.is_available and result.version:
            config_manager.create_update_tool_config(tool_name, {"version": result.version})


def freeze_to_screen(tool_names: list[str], schema: models.SchemaType) -> None:
    """
    Capture the current version of a list of tools, write them to a temp config file,
    and print the 'cli-tools' section of the config.

    Args:
        tool_names (list[str]): A list of tool names.
        schema (SchemaType): The schema to use for the version.
    """
    results = freeze_requirements(tool_names, schema=schema)

    # Create a temporary directory and file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = os.path.join(temp_dir, "temp.toml")
        config_manager = cm.ConfigManager(Path(temp_config_path))
        config_manager.read_config()

        for tool_name, result in results.items():
            if result.is_available and result.version:
                config_manager.create_update_tool_config(tool_name, {"version": result.version})

        # Save the config
        # pylint: disable=protected-access
        config_manager._save_config()

        # Read and print the content of the config file
        with open(temp_config_path, encoding="utf-8") as file:
            config_content = file.read()
            print(config_content)


if __name__ == "__main__":
    freeze_to_screen(["python", "pip", "poetry"], schema=models.SchemaType.SNAPSHOT)
```
## File: interactive.py
```python
"""
Interactively manage tool configurations.
"""

from typing import Union

import cli_tool_audit.config_manager as cm
from cli_tool_audit.models import SchemaType


def interactive_config_manager(config_manager: cm.ConfigManager) -> None:
    """
    Interactively manage tool configurations.

    Args:
        config_manager (ConfigManager): The configuration manager instance.
    """
    while True:
        print("\nCLI Tool Configuration Manager")
        print("1. Create or update tool configuration")
        print("2. Delete tool configuration")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            tool_name = input("\nEnter the name of the tool or enter to accept default: ")
            config: dict[str, Union[str, SchemaType]] = {}

            # Check existence only
            only_check_existence = input("Check existence only? (yes/no) Default no: ").lower()
            if only_check_existence.startswith("y"):
                config["schema"] = SchemaType.EXISTENCE

            if not only_check_existence.startswith("y"):
                # Schema
                schema = input("Enter schema, semver or snapshot (default is semver): ")
                if schema:
                    config["schema"] = SchemaType[schema.upper()]

                # Version
                if schema != "snapshot":
                    version = input("Enter the desired version (default is *, any version): ")
                    if version:
                        config["version"] = version

            # Version switch
            version_switch = input("Enter the version switch (default is --version): ")
            if version_switch:
                config["version_switch"] = version_switch

            #
            # OS-specific
            if_os = input(
                "Enter OS restriction, aix, emscripten, linux, wasi, win32, cygwin, darwin, etc. (default is all platforms): "
            )
            if if_os:
                config["if_os"] = if_os

            config_manager.create_update_tool_config(tool_name, config)
            print(f"Configuration for '{tool_name}' updated.")

        elif choice == "2":
            tool_name = input("\nEnter the name of the tool to delete: ")
            config_manager.delete_tool_config(tool_name)
            print(f"Configuration for '{tool_name}' deleted.")

        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")


# Example usage
# config_manager = ConfigManager("path_to_your_config.toml")
# interactive_config_manager(config_manager)
```
## File: json_utils.py
```python
"""
JSON utility functions.
"""

import dataclasses
import enum
from datetime import date, datetime
from typing import Any


def custom_json_serializer(o: Any) -> Any:
    """
    Custom JSON serializer for objects not serializable by default json code.

    Args:
        o (Any): The object to serialize.

    Returns:
        Any: A JSON serializable representation of the object.

    Raises:
        TypeError: If the object is not serializable.
    """
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if dataclasses.is_dataclass(o):
        return dataclasses.asdict(o)  # type: ignore
    if isinstance(o, enum.Enum):
        return o.value
    # Development time
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")
    # Production time
    # return str(o)


# def json_to_enum(cls, json_obj):
#     if isinstance(json_obj, dict):
#         for key, value in json_obj.items():
#             if isinstance(value, str) and key == 'schema':
#                 json_obj[key] = SchemaType(value)
#     return cls(**json_obj)
```
## File: known_switches.py
```python
"""
This file contains a dictionary of known switches for various CLI tools.
"""

KNOWN_SWITCHES = {
    "npm": "version",
    "terraform": "-version",  # modern versions also support --version
    "java": "-version",  # modern versions also support --version
}
```
## File: logging_config.py
```python
"""
Logging configuration.
"""

import os
from typing import Any


def generate_config(level: str = "DEBUG") -> dict[str, Any]:
    """
    Generate a logging configuration.
    Args:
        level: The logging level.

    Returns:
        dict: The logging configuration.
    """
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {"format": "[%(levelname)s] %(name)s: %(message)s"},
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(levelname)-8s%(reset)s %(green)s%(message)s",
            },
        },
        "handlers": {
            "default": {
                "level": "DEBUG",
                "formatter": "colored",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",  # Default is stderr
            },
        },
        "loggers": {
            "cli_tool_audit": {
                "handlers": ["default"],
                "level": "DEBUG",
                "propagate": False,
            }
        },
    }
    if os.environ.get("NO_COLOR") or os.environ.get("CI"):
        config["handlers"]["default"]["formatter"] = "standard"
    return config
```
## File: models.py
```python
"""
This module contains dataclasses for the tool audit.
"""

import datetime
import enum
import hashlib
from dataclasses import asdict, dataclass


class SchemaType(enum.Enum):
    SNAPSHOT = "snapshot"
    """Version is entire output of --version switch. Compatibility is by exact match."""
    SEMVER = "semver"
    """Major, minor, patch, pre-release, and build metadata. Compatibility is by specification."""
    PEP440 = "pep440"
    """Superficially looks like a superset of semver. As governed by PEP440."""
    EXISTENCE = "existence"
    """Only check if the tool exists. No version check. If it exists, it is compatible."""

    def __str__(self):
        return self.value


@dataclass
class CliToolConfig:
    """
    Represents what tool and what version the user wants to audit on their system.
    """

    name: str
    """Tool name without path"""
    version: str | None = None
    """Desired version"""
    version_switch: str | None = None
    """Command line switch to get version, e.g. -V, --version, etc."""
    schema: SchemaType | None = None
    """Snapshot, semver, pep440, existence"""
    if_os: str | None = None
    """Which OS this tool is needed for. Single value. Comparison evaluated by prefix. Same values as sys.platform"""
    tags: list[str] | None = None
    install_command: str | None = None
    """Having failed to find the right version what command can be run. Let the user run it."""
    install_docs: str | None = None
    """For failed tool checks, where can the user find out how to install."""

    def cache_hash(self) -> str:
        """
        Generate a hash for a CliToolConfig instance.

        Returns:
            str: The hash of the tool configuration.
        """
        config_str = ""
        for key, value in asdict(self).items():
            config_str += f"{key}={value};"  # Concatenate key-value pairs

        # Use hashlib to compute an MD5 hash of the concatenated string
        return hashlib.md5(config_str.encode()).hexdigest()  # nosec


@dataclass
class ToolCheckResult:
    """
    Represents the result of a tool check and version check.
    """

    tool: str
    desired_version: str
    is_needed_for_os: bool
    is_available: bool
    is_snapshot: bool
    """Snapshot schema"""
    found_version: str | None
    """Same as snapshot_version, the exact text produced by --version switch."""
    parsed_version: str | None
    """Clean stringification of the version object for current schema."""
    is_compatible: str
    is_broken: bool
    last_modified: datetime.datetime | None
    tool_config: CliToolConfig

    def status(self) -> str:
        """Compress many status fields into one for display
        Returns:
            str: The status of the tool.
        """
        # Status compression
        # Wrong OS. If wrong OS "Wrong OS"
        # Found/Not. If not found "Not Found"
        # If schema = existence, "Found"
        # Runnable/Not. If not, "Not Runnable"
        # Compatible/Not. If yes, "Compatible"
        # If no "Incompatible"
        if not self.is_needed_for_os:
            status = "Wrong OS"
        elif not self.is_available:
            status = "Not available"
        # need schema!
        elif self.tool_config.schema == "existence":
            status = "Available"
        elif self.is_broken:
            status = "Can't run"
        else:
            status = self.is_compatible
        return status

    def is_problem(self) -> bool:
        """Is this tool's state a problem?
        If it is needed for this OS, if it is incompatible or unavailable, it is a problem.

        Returns:
            bool: True if this tool's state is a problem, False otherwise.
        """
        missing_or_incompatible = self.is_compatible != "Compatible" or not self.is_available
        return self.is_needed_for_os and missing_or_incompatible


@dataclass
class ToolAvailabilityResult:
    """
    Represents only if the tool is available or not.
    """

    is_available: bool
    is_broken: bool
    version: str | None
    """Desired version"""
    last_modified: datetime.datetime | None


if __name__ == "__main__":
    # Example usage
    config = CliToolConfig(name="example_tool", version="1.0.0")
    print(config.cache_hash())
```
## File: policy.py
```python
"""
Apply various policies to the results of the tool checks.
"""

import cli_tool_audit.models as models


def apply_policy(results: list[models.ToolCheckResult]) -> bool:
    """
    Pretty print the results of the validation.

    Args:
        results (list[models.ToolCheckResult]): A list of ToolCheckResult objects.

    Returns:
        bool: True if any of the tools failed validation, False otherwise.
    """
    failed = False
    for result in results:
        if result.is_broken:
            failed = True
        elif not result.is_available:
            failed = True

        if not result.is_compatible:
            failed = True

    return failed
```
## File: py.typed
```
# when type checking dependents, tell type checkers to use this package's types
```
## File: version_parsing.py
```python
import logging
import re

import packaging.specifiers as ps
import packaging.version
import semver
from semver import Version

logger = logging.getLogger(__name__)


def extract_first_two_part_version(input_string: str) -> str | None:
    """
    Extract the first 2 part version from a string.
    Args:
        input_string (str): The string to parse.

    Returns:
        Optional[str]: The first 2 part version if found, None otherwise.

    Examples:
        >>> extract_first_two_part_version("1.2.3")
        '1.2'
        >>> extract_first_two_part_version("1.2")
        '1.2'
        >>> extract_first_two_part_version("1") is None
        True
        >>> extract_first_two_part_version("1.2.3a1")
        '1.2'
        >>> extract_first_two_part_version("1.2.3a1.post1")
        '1.2'
    """
    # Regular expression for 2 part version
    semver_regex = r"\d+\.\d+"

    # Find all matches in the string
    matches = re.findall(semver_regex, input_string)

    # Return the first match or None if no match is found
    return matches[0] if matches else None


def extract_first_semver_version(input_string: str) -> str | None:
    """
    Extract the first semver version from a string.
    Args:
        input_string (str): The string to parse.

    Returns:
        Optional[str]: The first semver version if found, None otherwise.

    Examples:
        >>> extract_first_semver_version("1.2.3")
        '1.2.3'
        >>> extract_first_semver_version("1.2") is None
        True
        >>> extract_first_semver_version("1.2.3a1")
        '1.2.3'
        >>> extract_first_semver_version("1.2.3a1.post1")
        '1.2.3'

    """
    # Regular expression for semver version
    semver_regex = r"\d+\.\d+\.\d+"

    # Find all matches in the string
    matches = re.findall(semver_regex, input_string)

    # Return the first match or None if no match is found
    return matches[0] if matches else None


# packaging.version.Version
def convert2semver(version: packaging.version.Version) -> semver.Version:
    """Converts a PyPI version into a semver version

    Args:
        version (packaging.version.Version): the PyPI version

    Returns:
        semver.Version: the semver version

    Raises:
        ValueError: if epoch or post parts are used
    """
    if version.epoch:
        raise ValueError("Can't convert an epoch to semver")
    if version.post:
        raise ValueError("Can't convert a post part to semver")

    pre = None if not version.pre else "".join([str(i) for i in version.pre])

    if len(version.release) == 3:
        major, minor, patch = version.release
        return semver.Version(major, minor, patch, prerelease=pre, build=version.dev)
    major, minor = version.release
    return semver.Version(major, minor, prerelease=pre, build=version.dev)


def two_pass_semver_parse(input_string: str) -> Version | None:
    """
    Parse a string into a semver version. This function will attempt to parse the string twice.
    The first pass will attempt to parse the string as a semver version. If that fails, the second pass will attempt to
    parse the string as a PyPI version. If that fails, the third pass will attempt to parse the string as a 2 part
    version. If that fails, the fourth pass will attempt to parse the string as a 1 part version. If that fails, None
    is returned.

    Args:
        input_string (str): The string to parse.

    Returns:
        Optional[Version]: A semver version if the string can be parsed, None otherwise.

    Examples:
        >>> two_pass_semver_parse("1.2.3")
        Version(major=1, minor=2, patch=3, prerelease=None, build=None)
        >>> two_pass_semver_parse("1.2")
        Version(major=1, minor=2, patch=0, prerelease=None, build=None)
        >>> two_pass_semver_parse("1.2.3a1")
        Version(major=1, minor=2, patch=3, prerelease='a1', build=None)
        >>> two_pass_semver_parse("1.2.3a1.post1")
        Version(major=1, minor=2, patch=3, prerelease=None, build=None)
    """
    # empty never works
    if not input_string:
        return None

    # Clean semver string
    try:
        possible = Version.parse(input_string)
        return possible
    except ValueError:
        logging.debug(f"Value Error: Failed to parse {input_string} as semver")
    except TypeError:
        logging.debug(f"Type Error: Failed to parse {input_string} as semver")

    # Clean pypi version, including 2 part versions

    # pylint: disable=broad-exception-caught
    try:
        pypi_version = ps.Version(input_string)
        possible = convert2semver(pypi_version)
        if possible:
            return possible
    except BaseException:
        logging.debug(f"ps.Version/convert2semver: Failed to parse {input_string} as semver")

    possible_first = extract_first_semver_version(input_string)
    if possible_first:
        try:
            possible = Version.parse(possible_first)
            return possible
        except ValueError:
            logging.debug(f"Version.parse: Failed to parse {input_string} as semver")
        except TypeError:
            logging.debug(f"Version.parse: Failed to parse {input_string} as semver")

    possible_first = extract_first_two_part_version(input_string)
    if possible_first:
        try:
            pypi_version = ps.Version(possible_first)
            possible = convert2semver(pypi_version)
            return possible
        except ValueError:
            pass
        except TypeError:
            pass
    # Give up. This doesn't appear to be semver
    return None


if __name__ == "__main__":
    convert2semver(packaging.version.Version("1.2"))

    convert2semver(packaging.version.Version("1.2.3"))
```
## File: views.py
```python
"""
Main output view for cli_tool_audit assuming tool list is in config.
"""

import concurrent
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Union

import colorama
from prettytable import PrettyTable
from prettytable.colortable import ColorTable, Themes
from tqdm import tqdm

import cli_tool_audit.call_and_compatible as call_and_compatible
import cli_tool_audit.config_reader as config_reader
import cli_tool_audit.json_utils as json_utils
import cli_tool_audit.models as models
import cli_tool_audit.policy as policy

colorama.init(convert=True)

logger = logging.getLogger(__name__)


def validate(
    file_path: Path = Path("pyproject.toml"),
    no_cache: bool = False,
    tags: list[str] | None = None,
    disable_progress_bar: bool = False,
) -> list[models.ToolCheckResult]:
    """
    Validate the tools in the pyproject.toml file.

    Args:
        file_path (Path, optional): The path to the pyproject.toml file. Defaults to "pyproject.toml".
        no_cache (bool, optional): If True, don't use the cache. Defaults to False.
        tags (Optional[list[str]], optional): Only check tools with these tags. Defaults to None.
        disable_progress_bar (bool, optional): If True, disable the progress bar. Defaults to False.

    Returns:
        list[models.ToolCheckResult]: A list of ToolCheckResult objects.
    """
    if tags is None:
        tags = []
    cli_tools = config_reader.read_config(file_path)
    return process_tools(cli_tools, no_cache, tags, disable_progress_bar=disable_progress_bar)


def process_tools(
    cli_tools: dict[str, models.CliToolConfig],
    no_cache: bool = False,
    tags: list[str] | None = None,
    disable_progress_bar: bool = False,
) -> list[models.ToolCheckResult]:
    """
    Process the tools from a dictionary of CliToolConfig objects.

    Args:
        cli_tools (dict[str, models.CliToolConfig]): A dictionary of tool names and CliToolConfig objects.
        no_cache (bool, optional): If True, don't use the cache. Defaults to False.
        tags (Optional[list[str]], optional): Only check tools with these tags. Defaults to None.
        disable_progress_bar (bool, optional): If True, disable the progress bar. Defaults to False.

    Returns:
        list[models.ToolCheckResult]: A list of ToolCheckResult objects.
    """
    if tags:
        print(tags)
        cli_tools = {
            tool: config
            for tool, config in cli_tools.items()
            if config.tags and any(tag in config.tags for tag in tags)
        }

    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    enable_cache = len(cli_tools) >= 5
    # Create a ThreadPoolExecutor with one thread per CPU

    if no_cache:
        enable_cache = False
    lock = Lock()
    # Threaded appears faster.
    # lock = Dummy()
    # with ProcessPoolExecutor(max_workers=num_cpus) as executor:
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        disable = should_show_progress_bar(cli_tools)
        with tqdm(total=len(cli_tools), disable=disable) as pbar:
            # Submit tasks to the executor
            futures = [
                executor.submit(call_and_compatible.check_tool_wrapper, (tool, config, lock, enable_cache))
                for tool, config in cli_tools.items()
            ]
            results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                pbar.update(1)
                results.append(result)
    return results


def report_from_pyproject_toml(
    file_path: Path | None = Path("pyproject.toml"),
    config_as_dict: dict[str, models.CliToolConfig] | None = None,
    exit_code_on_failure: bool = True,
    file_format: str = "table",
    no_cache: bool = False,
    tags: list[str] | None = None,
    only_errors: bool = False,
    quiet: bool = False,
) -> int:
    """
    Report on the compatibility of the tools in the pyproject.toml file.

    Args:
        file_path (Path, optional): The path to the pyproject.toml file. Defaults to "pyproject.toml".
        config_as_dict (Optional[dict[str, models.CliToolConfig]], optional): A dictionary of tool names and CliToolConfig objects. Defaults to None.
        exit_code_on_failure (bool, optional): If True, exit with return value of 1 if validation fails. Defaults to True.
        file_format (str, optional): The format of the output. Defaults to "table".
        no_cache (bool, optional): If True, don't use the cache. Defaults to False.
        tags (Optional[list[str]], optional): Only check tools with these tags. Defaults to None.
        only_errors (bool, optional): Only show errors. Defaults to False.
        quiet (bool, optional): If True, suppress all output. Defaults to False.

    Returns:
        int: The exit code.
    """
    if tags is None:
        tags = []
    if not file_format:
        file_format = "table"

    if config_as_dict:
        results = process_tools(config_as_dict, no_cache, tags, disable_progress_bar=file_format != "table")
    elif file_path:
        # Handle config file searching.
        if not file_path.exists():
            one_up = ".." / file_path
            if one_up.exists():
                file_path = one_up
        results = validate(file_path, no_cache=no_cache, tags=tags, disable_progress_bar=file_format != "table")
    else:
        raise TypeError("Must provide either file_path or config_as_dict.")

    success_and_failure = len(results)
    # Remove success, no action needed.
    if only_errors:
        results = [result for result in results if result.is_problem()]

    failed = policy.apply_policy(results)

    if file_format == "quiet" or quiet:
        logger.debug("Quiet mode enabled, suppressing UI output. If you want no output at all, don't select --verbose")
    elif file_format == "json":
        print(json.dumps([result.__dict__ for result in results], indent=4, default=json_utils.custom_json_serializer))
    elif file_format == "json-compact":
        print(json.dumps([result.__dict__ for result in results], default=json_utils.custom_json_serializer))
    elif file_format == "xml":
        print("<results>")
        for result in results:
            print("  <result>")
            for key, value in result.__dict__.items():
                print(f"    <{key}>{value}</{key}>")
            print("  </result>")
        print("</results>")
    elif file_format == "table":
        table = pretty_print_results(results, truncate_long_versions=True, include_docs=False)
        print(table)
    elif file_format == "csv":
        print(
            "tool,desired_version,is_available,is_snapshot,found_version,parsed_version,is_compatible,is_broken,last_modified"
        )
        for result in results:
            print(
                f"{result.tool},{result.desired_version},{result.is_available},{result.is_snapshot},{result.found_version},{result.parsed_version},{result.is_compatible},{result.is_broken},{result.last_modified}"
            )
    elif file_format == "html":
        table = pretty_print_results(results, truncate_long_versions=False, include_docs=True)
        print(table.get_html_string())
    else:
        print(
            f"Unknown file format: {file_format}, defaulting to table output. Supported formats: json, json-compact, xml, table, csv."
        )
        table = pretty_print_results(results, truncate_long_versions=True, include_docs=False)
        print(table)

    if only_errors and success_and_failure > 0 and len(results) == 0:
        if not quiet:
            print("No errors found, all tools meet version policy.")
        return 0
    if failed and exit_code_on_failure and file_format == "table":
        if not quiet:
            print("Did not pass validation, failing with return value of 1.")
        return 1
    return 0


def pretty_print_results(
    results: list[models.ToolCheckResult], truncate_long_versions: bool, include_docs: bool
) -> Union[PrettyTable, ColorTable]:
    """
    Pretty print the results of the validation.

    Args:
        results (list[models.ToolCheckResult]): A list of ToolCheckResult objects.
        truncate_long_versions (bool): If True, truncate long versions. Defaults to False.
        include_docs (bool): If True, include install command and install docs. Defaults to False.

    Returns:
        Union[PrettyTable, ColorTable]: A PrettyTable or ColorTable object.
    """
    if os.environ.get("NO_COLOR") or os.environ.get("CI"):
        table = PrettyTable()
    else:
        table = ColorTable(theme=Themes.OCEAN)
    table.field_names = ["Tool", "Found", "Parsed", "Desired", "Status", "Modified"]
    if include_docs:
        table.field_names.append("Install Command")
        table.field_names.append("Install Docs")

    all_rows: list[list[str]] = []

    for result in results:
        if truncate_long_versions:
            found_version = result.found_version[0:25].strip() if result.found_version else ""
        else:
            found_version = result.found_version or ""

        try:
            last_modified = result.last_modified.strftime("%m/%d/%y") if result.last_modified else ""
        except ValueError:
            last_modified = str(result.last_modified)
        row_data = [
            result.tool,
            found_version or "",
            result.parsed_version if result.parsed_version else "",
            result.desired_version or "",
            # "Yes" if result.is_compatible == "Compatible" else result.is_compatible,
            result.status() or "",
            last_modified,
        ]
        if include_docs:
            row_data.append(result.tool_config.install_command or "")
            row_data.append(result.tool_config.install_docs or "")
        row_transformed = []
        for datum in row_data:
            if result.is_problem():
                transformed = f"{colorama.Fore.RED}{datum}{colorama.Style.RESET_ALL}"
            else:
                transformed = str(datum)
            row_transformed.append(transformed)
        all_rows.append(row_transformed)

    table.add_rows(sorted(all_rows, key=lambda x: x[0]))

    return table


def should_show_progress_bar(cli_tools) -> bool | None:
    """
    Determine if a progress bar should be shown.

    Args:
        cli_tools: A dictionary of tool names and CliToolConfig objects.

    Returns:
        Optional[bool]: True if the progress bar should be shown, False if it should be hidden, or None if it can't be determined
    """
    disable = len(cli_tools) < 5 or os.environ.get("CI") or os.environ.get("NO_COLOR")
    return True if disable else None


if __name__ == "__main__":
    report_from_pyproject_toml()
```
## File: view_npm_stress_test.py
```python
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
```
## File: view_pipx_stress_test.py
```python
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

    def __enter__(self) -> None:
        """For testing"""

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """For testing
        Args:
            exc_type (Any): For testing
            exc_value (Any): For testing
            traceback (Any): For testing
        """


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
```
## File: view_venv_stress_test.py
```python
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
        print(views.pretty_print_results(results, truncate_long_versions=True, include_docs=False))


if __name__ == "__main__":
    report_for_venv_tools()
```
## File: __about__.py
```python
"""Metadata for cli_tool_audit."""

__all__ = [
    "__title__",
    "__version__",
    "__description__",
    "__credits__",
    "__readme__",
    "__requires_python__",
    "__keywords__",
    "__status__",
]

__title__ = "cli_tool_audit"
__version__ = "3.1.0"
__description__ = "Audit for existence and version number of cli tools."
__credits__ = [{"name": "Matthew Martin", "email": "matthewdeanmartin@gmail.com"}]
__readme__ = "README.md"
__requires_python__ = ">=3.9"
__keywords__ = ["cli tooling", "version numbers"]
__status__ = "4 - Beta"
```
## File: __main__.py
```python
"""
Argument parsing code.
"""

import argparse
import logging
import logging.config
import sys
from collections.abc import Sequence
from dataclasses import fields
from pathlib import Path
from typing import Any

import cli_tool_audit.config_manager as config_manager
import cli_tool_audit.freeze as freeze
import cli_tool_audit.interactive as interactive
import cli_tool_audit.logging_config as logging_config
import cli_tool_audit.models as models
import cli_tool_audit.view_npm_stress_test as demo_npm
import cli_tool_audit.view_pipx_stress_test as demo_pipx
import cli_tool_audit.view_venv_stress_test as demo_venv
import cli_tool_audit.views as views
from cli_tool_audit.__about__ import __description__, __version__

logger = logging.getLogger(__name__)


def handle_read(args: argparse.Namespace) -> None:
    """
    Read and list all tool configurations
    Args:
        args: The args from the command line.
    """
    manager = config_manager.ConfigManager(Path(args.config))
    manager.read_config()
    for tool, config in manager.tools.items():
        print(f"{tool}")
        for key, value in vars(config).items():
            if value is not None:
                print(f"  {key}: {value}")


def handle_create(args: argparse.Namespace) -> None:
    """
    Create a new tool configuration.
    Args:
        args: The args from the command line.
    """
    kwargs = reduce_args_tool_cli_tool_config_args(args)

    manager = config_manager.ConfigManager(Path(args.config))
    manager.create_tool_config(args.tool, kwargs)
    print(f"Tool {args.tool} created.")


def reduce_args_tool_cli_tool_config_args(args: argparse.Namespace) -> dict[str, Any]:
    """
    Reduce the args to only those that are in CliToolConfig.
    Args:
        args: The args from the command line.

    Returns:
        dict: The reduced args.
    """
    kwargs = {}
    args_dict = vars(args)
    cli_tool_fields = {f.name for f in fields(models.CliToolConfig)}
    for key, value in args_dict.items():
        if key in cli_tool_fields:
            kwargs[key] = value
    return kwargs


def handle_update(args: argparse.Namespace) -> None:
    kwargs = reduce_args_tool_cli_tool_config_args(args)
    manager = config_manager.ConfigManager(Path(args.config))
    manager.update_tool_config(args.tool, {k: v for k, v in kwargs.items() if k != "tool"})
    print(f"Tool {args.tool} updated.")


def handle_delete(args: argparse.Namespace) -> None:
    """
    Delete a tool configuration.
    Args:
        args: The args from the command line.
    """
    manager = config_manager.ConfigManager(Path(args.config))
    manager.delete_tool_config(args.tool)
    print(f"Tool {args.tool} deleted.")


def handle_interactive(args: argparse.Namespace) -> None:
    """
    Interactively edit configuration from terminal.
    Args:
        args: The args from the command line.
    """
    manager = config_manager.ConfigManager(Path(args.config))
    interactive.interactive_config_manager(manager)


def add_update_args(parser: argparse.ArgumentParser) -> None:
    """
    Add arguments to the add or update parser.
    Args:
        parser: The add or update parser.
    """
    parser.add_argument("--version", help="Version of the tool")
    parser.add_argument("--version-switch", "--version_switch", help="Version switch for the tool")
    add_schema_argument(parser)
    parser.add_argument("--if-os", help="Check only on this os.")

    # TODO: Add more arguments


def handle_audit(args: argparse.Namespace) -> None:
    """
    Audit environment with current configuration.

    Args:
        args: The args from the command line.
    """
    views.report_from_pyproject_toml(
        file_path=Path(args.config),
        exit_code_on_failure=not args.never_fail,
        file_format=args.format,
        no_cache=args.no_cache,
        tags=args.tags,
        only_errors=args.only_errors,
        quiet=args.quiet,
    )


def handle_single(args):
    """
    Audit environment with current configuration.

    Args:
        args: The args from the command line.
    """
    config = models.CliToolConfig(
        name=args.tool, version=args.version, version_switch=args.version_switch, schema=args.schema, if_os=args.if_os
    )
    views.report_from_pyproject_toml(
        file_path=None,
        config_as_dict={args.tool: config},
        exit_code_on_failure=True,
        file_format=args.format,
        no_cache=False,
        tags=None,
        only_errors=False,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the CLI tool.
    Args:
        argv: The arguments to parse.

    Returns:
        int: The exit code.
    """
    # Create the parser
    program = "cli_tool_audit"
    parser = argparse.ArgumentParser(
        prog=program,
        allow_abbrev=False,
        description=__description__,
        epilog=f"""
    Examples:

        # Audit and report using pyproject.toml
        {program} audit
        
        # Generate config for snapshots
        {program} freeze python java make rustc
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit.",
    )

    parser.add_argument("--verbose", action="store_true", help="verbose output")

    parser.add_argument("--quiet", action="store_true", help="suppress output")

    parser.add_argument(
        "--demo",
        type=str,
        choices=("pipx", "venv", "npm"),
        help="Demo for values of npm, pipx or venv",
    )

    subparsers = parser.add_subparsers(help="Subcommands.")

    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Interactively edit configuration")
    add_config_to_subparser(interactive_parser)
    interactive_parser.set_defaults(func=handle_interactive)

    # Add 'freeze' sub-command
    freeze_parser = subparsers.add_parser("freeze", help="Freeze the versions of specified tools")
    freeze_parser.add_argument("tools", nargs="+", help="List of tool names to freeze")
    add_schema_argument(freeze_parser)
    add_config_to_subparser(freeze_parser)

    # Add 'audit' sub-command
    audit_parser = subparsers.add_parser("audit", help="Audit environment with current configuration")
    add_formats(audit_parser)
    add_config_to_subparser(audit_parser)
    audit_parser.add_argument("-nf", "--never-fail", action="store_true", help="Never return a non-zero exit code")
    audit_parser.add_argument(
        "-nc",
        "--no-cache",
        action="store_true",
        help="Disable caching of results.",
    )
    audit_parser.add_argument(
        "-oe",
        "--only-errors",
        action="store_true",
        help="Show only tools in error.",
    )

    audit_parser.add_argument(
        "--tags",
        # action='append',
        nargs="+",
        help="Tag for filtering tools.",
    )
    audit_parser.set_defaults(func=handle_audit)

    # Single audit
    single_parser = subparsers.add_parser("single", help="Audit one tool without configuration file")
    single_parser.add_argument("tool", help="Name of the tool")
    single_parser.add_argument("--version", help="Version of the tool")
    single_parser.add_argument("--version-switch", "--version_switch", help="Version switch for the tool")
    add_schema_argument(single_parser)
    add_formats(single_parser)
    single_parser.add_argument("--if-os", help="Check only on this os.")
    single_parser.set_defaults(func=handle_single)

    # Read command
    read_parser = subparsers.add_parser("read", help="Read and list all tool configurations")
    add_config_to_subparser(read_parser)
    read_parser.set_defaults(func=handle_read)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new tool configuration")
    create_parser.add_argument("tool", help="Name of the tool")
    add_update_args(create_parser)
    add_config_to_subparser(create_parser)
    create_parser.set_defaults(func=handle_create)

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an existing tool configuration")
    update_parser.add_argument("tool", help="Name of the tool")
    add_config_to_subparser(update_parser)
    add_update_args(update_parser)

    update_parser.set_defaults(func=handle_update)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a tool configuration")
    delete_parser.add_argument("tool", help="Name of the tool")
    add_config_to_subparser(delete_parser)
    delete_parser.set_defaults(func=handle_delete)

    # --------------------------------------------------------------------------

    # Parse the arguments
    args = parser.parse_args(argv)

    if args.verbose:
        config = logging_config.generate_config(level="DEBUG")
        logging.config.dictConfig(config)
    else:
        # Essentially, quiet mode
        logging.basicConfig(level=logging.FATAL)

    logger.debug(f"command line args: {args}")

    # Demos
    if args.demo and args.demo == "pipx":
        demo_pipx.report_for_pipx_tools()
        return 0
    if args.demo and args.demo == "venv":
        demo_venv.report_for_venv_tools()
        return 0
    if args.demo and args.demo == "npm":
        demo_npm.report_for_npm_tools()
        return 0

    if hasattr(args, "func"):
        args.func(args)
        return 0

    # Namespace doesn't have word "freeze" in it.
    if hasattr(args, "tools") and args.tools:
        freeze.freeze_to_screen(args.tools, args.schema)
        return 0

    # Audit

    # Default behavior
    if not args.quiet:
        print("No command specified. Auditing environment with pyproject.toml configuration.")
    file_format = "quiet" if args.quiet else "table"
    return views.report_from_pyproject_toml(
        exit_code_on_failure=True, file_format=file_format, no_cache=True, quiet=args.quiet
    )


def add_formats(audit_parser):
    audit_parser.add_argument(
        "-f",
        "--format",
        default="table",
        type=str,
        choices=("json", "json-compact", "xml", "table", "csv", "html"),
        help="Output results in the specified format. (default is %(default)s)",
    )


def add_schema_argument(parser):
    parser.add_argument(
        "--schema", choices=("semver", "snapshot", "pep440", "existence"), default="snapshot", help="version schema"
    )


def add_config_to_subparser(interactive_parser):
    interactive_parser.add_argument(
        "-c",
        "--config",
        default="pyproject.toml",
        type=str,
        help="Path to the configuration file in TOML format. (default is %(default)s)",
    )


if __name__ == "__main__":
    sys.exit(main(["audit"]))
```
## File: .cli_tool_audit_cache\.gitignore
```
*
!.gitignore
```
## File: .cli_tool_audit_cache\black_b780445aca8bc5b17141b30522c5ab07.json
```json
{
    "tool": "black",
    "desired_version": ">=1.0.0",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "black, 24.4.2 (compiled: yes)\nPython (CPython) 3.12.0",
    "parsed_version": "24.4.2",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-05-26T13:32:41.433711",
    "tool_config": {
        "name": "black",
        "version": ">=1.0.0",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": null,
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\choco_acb3ff132133b4cc638f6fd3018b4c06.json
```json
{
    "tool": "choco",
    "desired_version": ">=0.10.13",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "2.3.0",
    "parsed_version": "2.3.0",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-06-05T12:09:28",
    "tool_config": {
        "name": "choco",
        "version": ">=0.10.13",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": null,
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\isort_9e6fb3e24115e8a8f0bb663f57bbb590.json
```json
{
    "tool": "isort",
    "desired_version": ">=5.0.0",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "_                 _\n                (_) ___  ___  _ __| |_\n                | |/ _/ / _ \\/ '__  _/\n                | |\\__ \\/\\_\\/| |  | |_\n                |_|\\___/\\___/\\_/   \\_/\n\n      isort your imports, so you don't have to.\n\n                    VERSION 5.13.2",
    "parsed_version": "5.13.2",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-05-26T13:32:39.746123",
    "tool_config": {
        "name": "isort",
        "version": ">=5.0.0",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": null,
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\make_aaf0418d3e8d542791533a3944488d8e.json
```json
{
    "tool": "make",
    "desired_version": ">=3.81",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "GNU Make 3.81\nCopyright (C) 2006  Free Software Foundation, Inc.\nThis is free software; see the source for copying conditions.\nThere is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A\nPARTICULAR PURPOSE.\n\nThis program built for i386-pc-mingw32",
    "parsed_version": "3.81.0",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2006-11-24T20:28:04",
    "tool_config": {
        "name": "make",
        "version": ">=3.81",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": [
            "build"
        ],
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\mypy_0731164ae5719aacbaf5b9bd18660c49.json
```json
{
    "tool": "mypy",
    "desired_version": ">=1.0.0",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "mypy 1.11.0 (compiled: yes)",
    "parsed_version": "1.11.0",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-07-27T13:31:36.840533",
    "tool_config": {
        "name": "mypy",
        "version": ">=1.0.0",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": [
            "build",
            "work"
        ],
        "install_command": "pipx install mypy",
        "install_docs": "https://mypy.readthedocs.io/en/stable/getting_started.html"
    }
}
```
## File: .cli_tool_audit_cache\notepad_81c010064e5fa8c52b1d30fc89cf925a.json
```json
{
    "tool": "notepad",
    "desired_version": "*",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": null,
    "parsed_version": "Found",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-06-16T22:12:43.577645",
    "tool_config": {
        "name": "notepad",
        "version": null,
        "version_switch": "--version",
        "schema": "existence",
        "if_os": null,
        "tags": null,
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\pygount_b829506909227e361210dd90697e7ade.json
```json
{
    "tool": "pygount",
    "desired_version": ">=1.6.0",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "pygount 1.8.0",
    "parsed_version": "1.8.0",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-08-02T17:03:47.755191",
    "tool_config": {
        "name": "pygount",
        "version": ">=1.6.0",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": null,
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\pylint_195df294ec23295b922c4011d09c6aaa.json
```json
{
    "tool": "pylint",
    "desired_version": ">=1.0.0",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "pylint 3.2.6\nastroid 3.2.4\nPython 3.12.0 (tags/v3.12.0:0fb18b0, Oct  2 2023, 13:03:39) [MSC v.1935 64 bit (AMD64)]",
    "parsed_version": "3.2.6",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-07-27T13:31:36.456282",
    "tool_config": {
        "name": "pylint",
        "version": ">=1.0.0",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": [
            "build",
            "work",
            "user"
        ],
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\python_0d9f3f4b30033fd9f79a0d9320ba927a.json
```json
{
    "tool": "python",
    "desired_version": ">=3.11.1",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "Python 3.12.0",
    "parsed_version": "3.12.0",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-05-26T13:32:10.918127",
    "tool_config": {
        "name": "python",
        "version": ">=3.11.1",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": [
            "build"
        ],
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\ruff_ce4b361277f65c4e5a2085ac37c6d60e.json
```json
{
    "tool": "ruff",
    "desired_version": "0.*",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "ruff 0.5.5",
    "parsed_version": "0.5.5",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-07-27T13:31:36.628630",
    "tool_config": {
        "name": "ruff",
        "version": "0.*",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": null,
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\rustc_c954c6d8cb8e4f417b8451828a5ba165.json
```json
{
    "tool": "rustc",
    "desired_version": ">=1.67.0",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "rustc 1.78.0 (9b00956e5 2024-04-29)",
    "parsed_version": "1.78.0",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-05-26T13:24:30.281327",
    "tool_config": {
        "name": "rustc",
        "version": ">=1.67.0",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": null,
        "install_command": null,
        "install_docs": null
    }
}
```
## File: .cli_tool_audit_cache\vulture_15cb5fd387564687965ebc69ee51020a.json
```json
{
    "tool": "vulture",
    "desired_version": "*",
    "is_needed_for_os": true,
    "is_available": true,
    "is_snapshot": false,
    "found_version": "vulture 2.11",
    "parsed_version": "2.11.0",
    "is_compatible": "Compatible",
    "is_broken": false,
    "last_modified": "2024-05-27T10:20:03.093483",
    "tool_config": {
        "name": "vulture",
        "version": "*",
        "version_switch": "--version",
        "schema": "semver",
        "if_os": null,
        "tags": null,
        "install_command": null,
        "install_docs": null
    }
}
```
