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

    def _uses_existence_schema(self) -> bool:
        schema = self.tool_config.schema
        return schema == SchemaType.EXISTENCE or schema == "existence"

    def failure_reason(self) -> str:
        """
        Produce a short, human-readable reason for the current result state.

        Returns:
            str: The concise reason string.
        """
        if not self.is_needed_for_os:
            return "wrong os"
        if not self.is_available:
            return "not found"
        if self._uses_existence_schema():
            return "available"
        if self.is_broken:
            return "broken"
        compatibility = (self.is_compatible or "").strip()
        if compatibility == "Compatible":
            return "compatible"
        if compatibility == "Can't tell":
            return "unknown version"
        if compatibility == "Not Found":
            return "not found"
        if compatibility == "different":
            return "different version"
        if " != " in compatibility:
            desired_version, found_version = compatibility.split(" != ", 1)
            return f"outdated (have {found_version}, need {desired_version})"
        return compatibility.lower()

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
        reason = self.failure_reason()
        if reason == "wrong os":
            return "Wrong OS"
        if reason == "not found":
            return "Not found"
        if reason == "available":
            return "Available"
        if reason == "broken":
            return "Broken (version check failed)"
        if reason == "compatible":
            return "Compatible"
        if reason == "unknown version":
            return "Unknown version"
        if reason == "different version":
            return "Different version"
        return reason[0].upper() + reason[1:] if reason else ""

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
