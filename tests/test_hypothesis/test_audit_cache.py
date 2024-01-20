# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.


import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import cli_tool_audit.audit_cache

#
# @given(cache_dir=st.one_of(st.none(), st.text()))
# def test_fuzz_AuditFacade(cache_dir: typing.Optional[str]) -> None:
#     cli_tool_audit.audit_cache.AuditFacade(cache_dir=cache_dir)


@pytest.mark.parametrize("cache_dir", [None, "subdir"])
@given(data=st.none())  # why do we need data?
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fuzz_AuditFacade(tmp_path, cache_dir, data):
    if cache_dir is not None:
        # Create a subdirectory or file in the temporary directory
        cache_dir = tmp_path / cache_dir
        cache_dir.mkdir(exist_ok=True)
    else:
        cache_dir = None

    # Call the function with the generated path or None
    cli_tool_audit.audit_cache.AuditFacade(cache_dir=cache_dir)
