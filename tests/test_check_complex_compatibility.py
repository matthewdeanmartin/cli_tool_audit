from semver import Version

from cli_tool_audit.compatibility_complex import check_range_compatibility, convert_version_range


def test_check_range_compatibility():
    assert check_range_compatibility("~1.0.0", Version(8, 32, 0)) == "~1.0.0 != 8.32.0"
    assert check_range_compatibility("^1.0.0", Version(1, 0, 1)) == "Compatible"


def test_convert_version_range():
    assert convert_version_range("*") == ">=0.0.0"
    assert convert_version_range("1.*") == ">=1.0.0 <2.0.0"
    assert convert_version_range("1.2.*") == ">=1.2.0 <1.3.0"
    assert convert_version_range("^1.2.3") == ">=1.2.3 <2.0.0"
    assert convert_version_range("~1.2") == ">=1.2 <1.3.0"
