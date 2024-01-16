import datetime
from dataclasses import dataclass
from typing import Optional

from semver import Version


@dataclass
class ToolCheckResult:
    tool: str
    desired_version: str
    is_available: bool
    is_snapshot: bool
    found_version: Optional[str]
    """Same as snapshot_version, the exact text produced by --version switch."""
    parsed_version: Optional[Version]
    """Semver parsed version."""
    is_compatible: str
    is_broken: bool
    last_modified: Optional[datetime.datetime]


@dataclass
class ToolAvailabilityResult:
    """
    Dataclass for the result of checking tool availability.
    """

    is_available: bool
    is_broken: bool
    version: Optional[str]
    last_modified: Optional[datetime.datetime]


@dataclass
class CliToolConfig:
    version: Optional[str] = None
    version_snapshot: Optional[str] = None
    version_switch: Optional[str] = None
    only_check_existence: Optional[bool] = False
    schema: Optional[str] = None
    if_os: Optional[str] = None
    version_stamp: Optional[str] = None
    source: Optional[str] = None
