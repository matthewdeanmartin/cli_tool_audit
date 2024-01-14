"""
Functions for checking compatibility between versions.
"""
import logging
import re
from typing import Any, Optional

from cli_tool_audit.version_parsing import two_pass_semver_parse

logger = logging.getLogger(__name__)


def split_version_match_pattern(pattern: str) -> tuple[str | Any, ...]:
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
        (None, '1.1.1')
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
    match_pattern_regex = r"(>=|<=|!=|>|<|==|~=)?(.*)"

    # Search for the pattern
    match = re.match(match_pattern_regex, pattern)

    # Return the comparator and version number if match is found
    if match:
        return match.groups()
    return None, None


CANT_TELL = "Can't tell"


def check_compatibility(desired_version: str, found_version: Optional[str]) -> str:
    """
    Check if a found version is compatible with a desired version. Uses semantic versioning.
    When a version isn't semver, we attempt to convert it to semver.

    Args:
        desired_version (str): The desired version.
        found_version (str): The found version.

    Returns:
        str: A string indicating if the versions are compatible or not.

    Examples:
        >>> check_compatibility(">=1.1.1", "1.1.1")
        'Compatible'
        >>> check_compatibility(">=1.1.1", "1.1.0")
        '>=1.1.1 != 1.1.0'
        >>> check_compatibility(">=1.1.1", "1.1.2")
        'Compatible'
    """
    if not found_version:
        logger.info(f"Tool provided no versions, so can't tell. {desired_version}/{found_version}")
        return CANT_TELL

    # desired is a match expression, e.g. >=1.1.1

    # Handle non-semver match patterns
    symbols, desired_version_text = split_version_match_pattern(desired_version)
    clean_desired_version = two_pass_semver_parse(desired_version_text)
    if clean_desired_version:
        desired_version = f"{symbols}{clean_desired_version}"

    try:
        found_semversion = two_pass_semver_parse(found_version)
        if found_semversion is None:
            logger.warning(f"SemVer failed to parse {desired_version}/{found_version}")
            is_compatible = CANT_TELL
        elif found_semversion.match(desired_version):
            is_compatible = "Compatible"
        else:
            is_compatible = f"{desired_version} != {found_semversion}"
    except ValueError as ve:
        logger.warning(f"Can't tell {desired_version}/{found_version}: {ve}")
        is_compatible = CANT_TELL
    except TypeError as te:
        logger.warning(f"Can't tell {desired_version}/{found_version}: {te}")
        is_compatible = CANT_TELL
    return is_compatible
