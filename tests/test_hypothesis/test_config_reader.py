# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

import cli_tool_audit.config_reader


@given(file_path=st.sampled_from([Path("."), Path("../pyproject.toml"), Path("audit.toml")]))
def test_fuzz_read_config(file_path: Path) -> None:
    cli_tool_audit.config_reader.read_config(file_path=file_path)
