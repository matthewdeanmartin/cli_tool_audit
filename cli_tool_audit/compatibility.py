import re
from typing import Any

from cli_tool_audit.version_parsing import two_pass_semver_parse


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


def check_compatibility(desired_version: str, found_version: str) -> str:
    # desired is a match expression, e.g. >=1.1.1

    # Handle non-semver match patterns
    symbols, desired_version_text = split_version_match_pattern(desired_version)
    clean_desired_version = two_pass_semver_parse(desired_version_text)
    if clean_desired_version:
        desired_version = f"{symbols}{clean_desired_version}"

    try:
        found_semversion = two_pass_semver_parse(found_version)
        if found_semversion is None:
            is_compatible = f"Can't tell {found_version}"
        elif found_semversion.match(desired_version):
            is_compatible = "Compatible"
        else:
            is_compatible = f"{desired_version} != {found_semversion}"
    except ValueError:
        is_compatible = "Can't tell"
    except TypeError:
        is_compatible = "Can't tell"
    return is_compatible
