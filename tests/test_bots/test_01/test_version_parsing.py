from unittest.mock import MagicMock, patch

import packaging.version
import pytest
import semver
from semver import Version

from cli_tool_audit.version_parsing import (
    convert2semver,
    extract_first_semver_version,
    extract_first_two_part_version,
    two_pass_semver_parse,
)


@pytest.mark.parametrize(
    "input_string, expected_version",
    [
        ("1.2.3", Version(major=1, minor=2, patch=3)),
        ("1.2", Version(major=1, minor=2, patch=0)),
        ("1.2.3a1", Version(major=1, minor=2, patch=3, prerelease="a1", build=None)),
        ("1.2.3a1.post1", Version(major=1, minor=2, patch=3)),
        ("not.a.version", None),  # Invalid version format
        ("1.2.3.4", Version(major=1, minor=2, patch=3)),  # Should still match first three parts
        ("2.0.0-beta", Version(major=2, minor=0, patch=0, prerelease="beta", build=None)),
        ("1.0.0+build.1", Version(major=1, minor=0, patch=0, prerelease=None, build="build.1")),
        ("", None),  # Empty string
    ],
)
def test_two_pass_semver_parse(input_string, expected_version):
    result = two_pass_semver_parse(input_string)

    # Convert expected_version to string for comparison if it's None
    if expected_version is None:
        assert result is None
    else:
        assert result == expected_version


def test_two_pass_semver_parse_exceptions():
    with patch("cli_tool_audit.version_parsing.Version.parse") as mock_parse:
        # Simulate a ValueError when trying to parse a semver version
        mock_parse.side_effect = ValueError("Invalid Version")
        result = two_pass_semver_parse("invalid_version")
        assert result is None  # Should return None on failure

    with patch("cli_tool_audit.version_parsing.ps.Version") as mock_ps_version:
        # Test when packaging.version raises ValueError during version creation
        mock_ps_version.side_effect = ValueError("Invalid PyPI Version")
        result = two_pass_semver_parse("some_pypi_version")
        assert result is None  # Should return None on failure

    with patch("cli_tool_audit.version_parsing.convert2semver") as mock_convert:
        # Test when convert2semver raises ValueError
        mock_convert.side_effect = ValueError("Cannot convert to semver")
        mock_ps_version.return_value = MagicMock(release=[1, 2])  # Mock a valid release format
        result = two_pass_semver_parse("1.2")
        assert result is None  # Should return None on failure

    with patch("cli_tool_audit.version_parsing.extract_first_semver_version") as mock_extract_semver:
        mock_extract_semver.return_value = None  # Simulate that no semver was found
        result = two_pass_semver_parse("random_string")
        assert result is None  # Should return None

    with patch("cli_tool_audit.version_parsing.extract_first_two_part_version") as mock_extract_two_part:
        mock_extract_two_part.return_value = None  # Simulate that no two-part version was found
        result = two_pass_semver_parse("another_random_string")
        assert result is None  # Should return None


def test_extract_first_two_part_version():
    assert extract_first_two_part_version("1.2.3") == "1.2"
    assert extract_first_two_part_version("1.2.3a1") == "1.2"
    assert extract_first_two_part_version("1.2.3a1.post1") == "1.2"
    assert extract_first_two_part_version("1.2") == "1.2"
    assert extract_first_two_part_version("1") is None
    assert extract_first_two_part_version("") is None
    assert extract_first_two_part_version("Some text") is None


def test_extract_first_semver_version():
    assert extract_first_semver_version("1.2.3") == "1.2.3"
    assert extract_first_semver_version("1.2.3a1") == "1.2.3"
    assert extract_first_semver_version("1.2.3a1.post1") == "1.2.3"
    assert extract_first_semver_version("1.2") is None
    assert extract_first_semver_version("1") is None
    assert extract_first_semver_version("") is None
    assert extract_first_semver_version("Some text") is None


def test_convert2semver():
    valid_version = packaging.version.Version("1.2.3")

    # Test happy path
    semver_version = convert2semver(valid_version)
    assert semver_version == semver.Version(1, 2, 3)

    # Test post parts raise ValueError
    invalid_version = packaging.version.Version("1.2.3.post1")
    with pytest.raises(ValueError):
        convert2semver(invalid_version)


def test_two_pass_semver_parse_happy_path():
    assert two_pass_semver_parse("1.2.3") == semver.Version(1, 2, 3)
    assert two_pass_semver_parse("1.2") == semver.Version(1, 2, 0)
    assert two_pass_semver_parse("1.2.3a1") == semver.Version(1, 2, 3, prerelease="a1")
    assert two_pass_semver_parse("1.2.3a1.post1") == semver.Version(1, 2, 3)


def test_two_pass_semver_parse_with_side_effects():
    with patch("cli_tool_audit.version_parsing.Version.parse") as mock_parse:
        # Happy path
        mock_parse.return_value = semver.Version(1, 2, 3)
        assert two_pass_semver_parse("1.2.3") == semver.Version(1, 2, 3)

        # Simulate a ValueError
        mock_parse.side_effect = ValueError("Invalid Version")
        result = two_pass_semver_parse("invalid_version")
        assert result is None

    with patch("cli_tool_audit.version_parsing.ps.Version") as mock_ps_version:
        # Test when packaging.version raises ValueError during version creation
        mock_ps_version.side_effect = ValueError("Invalid PyPI Version")
        result = two_pass_semver_parse("some_pypi_version")
        assert result is None

    with patch("cli_tool_audit.version_parsing.convert2semver") as mock_convert:
        mock_convert.side_effect = ValueError("Cannot convert to semver")
        mock_ps_version.return_value = MagicMock(release=[1, 2])  # Mock a valid release format
        result = two_pass_semver_parse("1.2")
        assert result is None
