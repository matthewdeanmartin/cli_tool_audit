import re

import pytest
from semver import Version

from cli_tool_audit.compatibility_complex import check_range_compatibility, convert_version_range


@pytest.mark.parametrize(
    "version_range, expected",
    [
        ("^1.2.3", ">=1.2.3 <2.0.0"),
        ("~1.2", ">=1.2 <1.3.0"),
        ("*", ">=0.0.0"),
        ("1.*", ">=1.0.0 <2.0.0"),
        ("1.2.*", ">=1.2.0 <1.3.0"),
    ],
)
def test_convert_version_range(version_range, expected):
    assert convert_version_range(version_range) == expected


@pytest.mark.parametrize(
    "desired_version, found_version, expected",
    [
        ("^1.1.1", Version.parse("1.1.1"), "Compatible"),
        ("^1.1.1", Version.parse("1.1.0"), "^1.1.1 != 1.1.0"),
        ("~1.2.0", Version.parse("1.2.5"), "Compatible"),
    ],
)
def test_check_range_compatibility(desired_version, found_version, expected):
    assert check_range_compatibility(desired_version, found_version) == expected


@pytest.mark.parametrize(
    "invalid_range",
    [
        "1.2",  # should start with ^ or ~
        "1.2.3.4",  # too many segments
    ],
)
def test_convert_version_range_invalid(invalid_range):
    with pytest.raises(ValueError, match=re.escape("Version range must start with ^ or ~")):
        convert_version_range(invalid_range)


def test_check_range_compatibility_invalid_range():
    # Test handling of invalid desired version in check_range_compatibility
    found_version = Version.parse("1.1.1")
    invalid_desired_version = "1.2"  # invalid format
    with pytest.raises(ValueError, match=re.escape("Version range must start with ^ or ~")):
        check_range_compatibility(invalid_desired_version, found_version)


def test_convert_version_range_happy_path():
    # Happy path tests for valid version ranges
    assert convert_version_range("^1.2.3") == ">=1.2.3 <2.0.0"
    assert convert_version_range("~1.2") == ">=1.2 <1.3.0"
    assert convert_version_range("1.*") == ">=1.0.0 <2.0.0"
    assert convert_version_range("1.2.*") == ">=1.2.0 <1.3.0"
    assert convert_version_range("*") == ">=0.0.0"


def test_convert_version_range_edge_cases():
    # Edge cases
    assert convert_version_range("^0.0.1") == ">=0.0.1 <1.0.0"
    assert convert_version_range("^0.1.2") == ">=0.1.2 <0.2.0"
    assert convert_version_range("~0.1.2") == ">=0.1.2 <0.2.0"


def test_convert_version_range_invalid2():
    # Invalid version range inputs
    invalid_ranges = [
        "1.2",  # should start with ^ or ~
        "1.2.3.4",  # too many segments
        "abc",  # completely invalid
        "",  # empty input
    ]

    for invalid_range in invalid_ranges:
        with pytest.raises(ValueError, match=re.escape("Version range must start with ^ or ~")):
            convert_version_range(invalid_range)


def test_check_range_compatibility_happy_path():
    # Happy path for compatible versions
    assert check_range_compatibility("^1.2.3", Version.parse("1.2.3")) == "Compatible"
    assert check_range_compatibility("^1.0.0", Version.parse("1.0.1")) == "Compatible"


def test_check_range_compatibility_edge_cases():
    # Edge cases for check_range_compatibility
    assert check_range_compatibility("^1.2.1", Version.parse("1.2.0")) == "^1.2.1 != 1.2.0"
    assert check_range_compatibility("^0.0.1", Version.parse("0.0.0")) == "^0.0.1 != 0.0.0"


def test_check_range_compatibility_invalid():
    # Invalid desired version scenarios
    found_version = Version.parse("1.1.1")
    invalid_desired_versions = [
        "1.2",  # invalid format, lacks ^ or ~
        "abc",  # completely invalid
        "",  # empty input
    ]

    for invalid_desired_version in invalid_desired_versions:
        with pytest.raises(ValueError, match=re.escape("Version range must start with ^ or ~")):
            check_range_compatibility(invalid_desired_version, found_version)
