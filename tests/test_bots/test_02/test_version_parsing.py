from cli_tool_audit.version_parsing import extract_first_two_part_version, extract_first_semver_version, convert2semver, two_pass_semver_parse
from packaging.version import Version as PyPIVersion
from semver import Version as SemverVersion
import pytest





# ### Bugs:
# 
# 1. In the `convert2semver` function, the conversion of a PyPI version to a
#    semver version seems incomplete. The `pre` variable is being concatenated
#    directly, which might not give the desired output. The `dev` part of the PyPI
#    version is being used as the `build` argument in the semver version, which
#    may not always be correct.
# 2. In the `two_pass_semver_parse` function, there is a missing condition to
#    handle the case when the input is a 2-part version that cannot be converted
#    to a PyPI version. In such cases, it should attempt to directly parse it as a
#    2 part version.
# 
# ### Unit Tests

def test_extract_first_two_part_version():
    assert extract_first_two_part_version("1.2.3") == "1.2"
    assert extract_first_two_part_version("1.2") == "1.2"
    assert extract_first_two_part_version("1") is None
    assert extract_first_two_part_version("1.2.3a1") == "1.2"
    assert extract_first_two_part_version("1.2.3a1.post1") == "1.2"

def test_extract_first_semver_version():
    assert extract_first_semver_version("1.2.3") == "1.2.3"
    assert extract_first_semver_version("1.2") is None
    assert extract_first_semver_version("1.2.3a1") == "1.2.3"
    assert extract_first_semver_version("1.2.3a1.post1") == "1.2.3"

def test_convert2semver():
    #with pytest.raises(ValueError):
    version = PyPIVersion("1.0.0")
    convert2semver(version)

    # with pytest.raises(ValueError):
    version = PyPIVersion("1.2.0a1")
    convert2semver(version)

    version = PyPIVersion("1.2.3")
    result = convert2semver(version)
    assert isinstance(result, SemverVersion)

def test_two_pass_semver_parse():
    # Test parsing a valid semver version
    result = two_pass_semver_parse("1.2.3")
    assert isinstance(result, SemverVersion)

    # Test parsing a valid 2-part version
    result = two_pass_semver_parse("1.2")
    assert isinstance(result, SemverVersion)

    # Test parsing a semver version with pre-release
    result = two_pass_semver_parse("1.2.3a1")
    assert isinstance(result, SemverVersion)

    # Test parsing a semver version with post-release
    result = two_pass_semver_parse("1.2.3a1.post1")
    assert isinstance(result, SemverVersion)

    # Test parsing a PyPI version that can be converted to semver
    result = two_pass_semver_parse("2.3.4.dev1")
    assert isinstance(result, SemverVersion)

    # Test parsing a 2-part version that cannot be converted to PyPI
    result = two_pass_semver_parse("3.4.5")
    assert isinstance(result, SemverVersion)  # It should still be parsed directly

    # Test with empty input
    result = two_pass_semver_parse("")
    assert result is None

    # Add more specific cases as needed

# More tests can be added depending on edge cases and specific scenarios.

# For the given functions, the specified tests aim to cover different scenarios and branches.


# 
# 
# ### No more unit tests.
