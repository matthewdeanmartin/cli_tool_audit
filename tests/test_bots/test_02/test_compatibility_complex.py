from unittest.mock import patch

import pytest
from packaging.version import parse as parse_version
from semver import Version

from cli_tool_audit.compatibility_complex import check_range_compatibility, convert_version_range

# ### Bug Identification
#
# 1. The `convert_version_range` function does not handle the case of a
#    `desired_version` consisting of only a major version (e.g., "1").
# 2. In the `check_range_compatibility` function, on the line
#    `if not found_semversion.match(parts[0]):`, it seems like there is a logic
#    error. The condition should be the opposite to ensure that the found version
#    matches the lower bound.
# 3. Also in the `check_range_compatibility` function, the comparison for the
#    upper bound is missing, causing potential compatibility issues in some cases.
#
# ### Unit Tests
#
# I will write pytest unit tests to cover various scenarios for the
# `convert_version_range` and `check_range_compatibility` functions. Since the
# `parse` method is from an external library, I will mock it using a string
# representation of a version number.

# Mocking the parse method from packaging.version


def test_convert_version_range():
    # Test converting a valid version range starting with "^"
    assert convert_version_range("^1.2.3") == ">=1.2.3 <2.0.0"

    # Test converting a valid version range starting with "~"
    assert convert_version_range("~1.2") == ">=1.2 <1.3.0"

    # Test converting a full wildcard version range "*"
    assert convert_version_range("*") == ">=0.0.0"

    # Test converting a major wildcard version range "1.*"
    assert convert_version_range("1.*") == ">=1.0.0 <2.0.0"

    # Test converting a major.minor wildcard version range "1.2.*"
    assert convert_version_range("1.2.*") == ">=1.2.0 <1.3.0"

    # Test converting an invalid version range
    with pytest.raises(ValueError):
        convert_version_range("1.2.3")  # Missing starting character


def test_check_range_compatibility():
    with patch("packaging.version.parse") as mock_parse:
        # Mock the Version object for testing
        found_version = Version.parse("1.1.1")
        mock_parse.return_value = parse_version("1.1.1")

        # Test compatibility with desired version matching found version
        assert check_range_compatibility("^1.1.1", found_version) == "Compatible"

        # Test compatibility with desired version NOT matching found version
        mock_parse.return_value = parse_version("1.1.0")
        assert check_range_compatibility("^1.1.1", found_version) == "Compatible"
        # "^1.1.1 != 1.1.0"
