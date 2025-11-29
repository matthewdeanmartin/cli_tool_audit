# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.


from hypothesis import given
from hypothesis import strategies as st

import cli_tool_audit.compatibility


@given(desired_version=st.text(), found_version=st.one_of(st.none(), st.text()))
def test_fuzz_check_compatibility(desired_version: str, found_version: str | None) -> None:
    cli_tool_audit.compatibility.check_compatibility(desired_version=desired_version, found_version=found_version)


@given(pattern=st.text())
def test_fuzz_split_version_match_pattern(pattern: str) -> None:
    cli_tool_audit.compatibility.split_version_match_pattern(pattern=pattern)
