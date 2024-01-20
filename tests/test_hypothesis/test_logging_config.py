# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import cli_tool_audit.logging_config


@given(level=st.text())
def test_fuzz_generate_config(level: str) -> None:
    cli_tool_audit.logging_config.generate_config(level=level)
