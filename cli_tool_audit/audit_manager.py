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
from typing import Literal, Optional

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
        self.result: Optional[VersionResult] = None

    def parse_version(self, version_string: str) -> Optional[Version]:
        """
        Parse a version string into a semver Version object.
        Args:
            version_string (str): The version string to parse.

        Returns:
            Optional[Version]: The parsed version or None if the version string is invalid.
        """
        return version_parsing.two_pass_semver_parse(version_string)

    def check_compatibility(self, desired_version: Optional[str]) -> VersionResult:
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
            desired_version (Optional[str]): The desired version. Ignored.

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

    def check_compatibility(self, desired_version: Optional[str]) -> VersionResult:
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

    def check_compatibility(self, desired_version: Optional[str]) -> VersionResult:
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
            existence_checker = ExistenceVersionChecker("Found" if result.is_available else "Not Found")
            version_result = existence_checker.check_compatibility("Found")
            compatibility_report = existence_checker.format_report("Found")
            desired_version = "*"
        elif config.schema == models.SchemaType.SNAPSHOT:
            snapshot_checker = SnapshotVersionChecker(result.version or "")
            version_result = snapshot_checker.check_compatibility(config.version)
            compatibility_report = snapshot_checker.format_report(config.version or "")
            desired_version = config.version or ""
        elif config.schema == "pep440":
            pep440_checker = Pep440VersionChecker(result.version or "")
            version_result = pep440_checker.check_compatibility(config.version or "0.0.0")
            compatibility_report = pep440_checker.format_report(config.version or "0.0.0")
            desired_version = config.version or "*"
        else:  # config.schema == "semver":
            semver_checker = SemVerChecker(result.version or "")
            version_result = semver_checker.check_compatibility(config.version)
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
            logger.warning(f"{tool_name} is not on path.")
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
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, shell=False, check=True
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
            logger.error(f"{tool_name} is not on path.")
            return models.ToolAvailabilityResult(False, True, None, last_modified)

        return models.ToolAvailabilityResult(True, is_broken, version, last_modified)

    def get_command_last_modified_date(self, tool_name: str) -> Optional[datetime.datetime]:
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
