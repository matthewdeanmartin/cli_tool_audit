"""
This module contains dataclasses for the tool audit.
"""
import datetime
import hashlib
from dataclasses import asdict, dataclass
from typing import Optional


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
    found_version: Optional[str]
    """Same as snapshot_version, the exact text produced by --version switch."""
    parsed_version: Optional[str]
    """Clean stringification of the version object for current schema."""
    is_compatible: str
    is_broken: bool
    last_modified: Optional[datetime.datetime]

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
    version: Optional[str]
    """Desired version"""
    last_modified: Optional[datetime.datetime]


@dataclass
class CliToolConfig:
    """
    Represents what tool and what version the user wants to audit on their system.
    """

    name: str
    version: Optional[str] = None
    version_snapshot: Optional[str] = None
    version_switch: Optional[str] = None
    only_check_existence: Optional[bool] = False
    schema: Optional[str] = None
    if_os: Optional[str] = None
    version_stamp: Optional[str] = None
    source: Optional[str] = None

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


if __name__ == "__main__":
    # Example usage
    config = CliToolConfig(name="example_tool", version="1.0.0")
    print(config.cache_hash())
