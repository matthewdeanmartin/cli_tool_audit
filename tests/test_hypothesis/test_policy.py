# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import cli_tool_audit.models
import cli_tool_audit.policy
from cli_tool_audit.models import CliToolConfig, ToolCheckResult


@given(
    results=st.lists(
        st.builds(
            ToolCheckResult,
            desired_version=st.text(),
            found_version=st.one_of(st.none(), st.text()),
            is_available=st.booleans(),
            is_broken=st.booleans(),
            is_compatible=st.text(),
            is_needed_for_os=st.booleans(),
            is_snapshot=st.booleans(),
            last_modified=st.one_of(st.none(), st.datetimes()),
            parsed_version=st.one_of(st.none(), st.text()),
            tool=st.text(),
            tool_config=st.builds(
                CliToolConfig,
                if_os=st.one_of(st.none(), st.one_of(st.none(), st.text())),
                install_command=st.one_of(st.none(), st.one_of(st.none(), st.text())),
                install_docs=st.one_of(st.none(), st.one_of(st.none(), st.text())),
                name=st.text(),
                schema=st.one_of(
                    st.none(),
                    st.one_of(st.none(), st.sampled_from(cli_tool_audit.models.SchemaType)),
                ),
                tags=st.one_of(st.none(), st.one_of(st.none(), st.lists(st.text()))),
                version=st.one_of(st.none(), st.one_of(st.none(), st.text())),
                version_switch=st.one_of(st.none(), st.one_of(st.none(), st.text())),
            ),
        )
    )
)
def test_fuzz_apply_policy(
    results: list[cli_tool_audit.models.ToolCheckResult],
) -> None:
    cli_tool_audit.policy.apply_policy(results=results)
