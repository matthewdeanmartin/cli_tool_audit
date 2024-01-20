# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import cli_tool_audit.call_tools
import cli_tool_audit.known_switches as ks
import cli_tool_audit.models

#
# @given(
#     tool_name=st.text(),
#     schema=st.sampled_from(cli_tool_audit.models.SchemaType),
#     version_switch=st.text(),
# )
# def test_fuzz_check_tool_availability(
#     tool_name: str, schema: cli_tool_audit.models.SchemaType, version_switch: str
# ) -> None:
#     cli_tool_audit.call_tools.check_tool_availability(
#         tool_name=tool_name, schema=schema, version_switch=version_switch
#     )

ks.KNOWN_SWITCHES = list(ks.KNOWN_SWITCHES.keys())


@given(tool_name=st.sampled_from(ks.KNOWN_SWITCHES))
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_fuzz_get_command_last_modified_date(tool_name: str) -> None:
    cli_tool_audit.call_tools.get_command_last_modified_date(tool_name=tool_name)
