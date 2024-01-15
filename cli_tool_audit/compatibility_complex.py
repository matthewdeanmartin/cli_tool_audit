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
    version_string = convert_version_range(desired_version)
    parts = version_string.split(" ")
    if len(parts) == 1:
        if not found_semversion.match(parts[0]):
            return f"{desired_version} != {found_semversion}"

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
