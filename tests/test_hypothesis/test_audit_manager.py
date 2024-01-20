# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import cli_tool_audit.audit_manager


@given(version_string=st.sampled_from(["Found", "Not Found"]))
def test_fuzz_ExistenceVersionChecker(version_string: str) -> None:
    cli_tool_audit.audit_manager.ExistenceVersionChecker(version_string=version_string)


@given(version_string=st.sampled_from(["0.1.2", "2.3.4"]))
def test_fuzz_Pep440VersionChecker(version_string: str) -> None:
    cli_tool_audit.audit_manager.Pep440VersionChecker(version_string=version_string)


@given(version_string=st.text())
def test_fuzz_SemVerChecker(version_string: str) -> None:
    cli_tool_audit.audit_manager.SemVerChecker(version_string=version_string)


@given(version_string=st.text())
def test_fuzz_SnapshotVersionChecker(version_string: str) -> None:
    cli_tool_audit.audit_manager.SnapshotVersionChecker(version_string=version_string)


@given(is_compatible=st.booleans(), clean_format=st.text())
def test_fuzz_VersionResult(is_compatible: bool, clean_format: str) -> None:
    cli_tool_audit.audit_manager.VersionResult(is_compatible=is_compatible, clean_format=clean_format)
