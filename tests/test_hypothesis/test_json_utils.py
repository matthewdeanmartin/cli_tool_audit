# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.
import typing

from hypothesis import given
from hypothesis import strategies as st

import cli_tool_audit.json_utils


@given(o=st.sampled_from(cli_tool_audit.models.SchemaType))
def test_fuzz_custom_json_serializer(o: typing.Any) -> None:
    cli_tool_audit.json_utils.custom_json_serializer(o=o)
