# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

import cli_tool_audit.version_parsing
import packaging.version
from hypothesis import given, strategies as st
from packaging.version import Version

# Random strings are not valid versions, duh.
# @given(version=st.builds(Version, version=st.text()))
# def test_fuzz_convert2semver(version: packaging.version.Version) -> None:
#     cli_tool_audit.version_parsing.convert2semver(version=version)


@given(input_string=st.text())
def test_fuzz_extract_first_semver_version(input_string: str) -> None:
    cli_tool_audit.version_parsing.extract_first_semver_version(
        input_string=input_string
    )


@given(input_string=st.text())
def test_fuzz_extract_first_two_part_version(input_string: str) -> None:
    cli_tool_audit.version_parsing.extract_first_two_part_version(
        input_string=input_string
    )


@given(input_string=st.text())
def test_fuzz_two_pass_semver_parse(input_string: str) -> None:
    cli_tool_audit.version_parsing.two_pass_semver_parse(input_string=input_string)
