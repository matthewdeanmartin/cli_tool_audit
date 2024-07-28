from unittest.mock import patch

import pytest
from semver import Version

from cli_tool_audit.compatibility import check_compatibility


@pytest.mark.parametrize(
    "desired_version, found_version, expected_message, expected_version",
    [
        (">=1.1.1", "1.1.1", "Compatible", Version(major=1, minor=1, patch=1)),
        (">=1.1.1", "1.1.0", "Compatible", Version(major=1, minor=1, patch=0)),
        (">=1.1.1", "1.1.2", "Compatible", Version(major=1, minor=1, patch=2)),
        ("*", "1.1.1", "Compatible", None),
        (">=1.0.0", None, "Can't tell", None),
        (">=1.1.1", "invalid_version", "Can't tell", None),
    ],
)
def test_check_compatibility(desired_version, found_version, expected_message, expected_version):
    with patch("cli_tool_audit.version_parsing.two_pass_semver_parse") as mock_parse:
        # Mocking the expected behavior of version parsing
        if found_version and "invalid_version" not in found_version:
            mock_parse.return_value = Version.parse(found_version)
        else:
            mock_parse.return_value = None

        # Call the function being tested
        result_message, result_version = check_compatibility(desired_version, found_version)

        # Assert the results
        assert result_message == expected_message
        assert result_version == expected_version


def test_check_compatibility2():
    # Happy path scenarios
    with patch(
        "cli_tool_audit.version_parsing.two_pass_semver_parse", side_effect=lambda x: Version.parse(x) if x else None
    ):
        assert check_compatibility(">=1.1.1", "1.1.1") == (
            "Compatible",
            Version(major=1, minor=1, patch=1, prerelease=None, build=None),
        )
        assert check_compatibility(">=1.1.1", "1.1.2") == (
            "Compatible",
            Version(major=1, minor=1, patch=2, prerelease=None, build=None),
        )
        assert check_compatibility("<2.0.0", "1.9.0") == (
            "Compatible",
            Version(major=1, minor=9, patch=0, prerelease=None, build=None),
        )
        assert check_compatibility("*", "1.0.0") == ("Compatible", None)
        assert check_compatibility("==1.2.3", "1.2.3") == (
            "Compatible",
            Version(major=1, minor=2, patch=3, prerelease=None, build=None),
        )
        assert check_compatibility("!=1.2.3", "1.2.4") == (
            "Compatible",
            Version(major=1, minor=2, patch=4, prerelease=None, build=None),
        )

    # Edge cases
    with patch(
        "cli_tool_audit.version_parsing.two_pass_semver_parse", side_effect=lambda x: Version.parse(x) if x else None
    ):
        assert check_compatibility("~1.2.3", "1.2.4") == (
            "Compatible",
            Version(major=1, minor=2, patch=4, prerelease=None, build=None),
        )

    # Testing wildcard and empty found version
    with patch("cli_tool_audit.version_parsing.two_pass_semver_parse", side_effect=lambda x: None):
        assert check_compatibility("*", None) == ("Compatible", None)
