# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

import datetime

from hypothesis import given
from hypothesis import strategies as st

import cli_tool_audit.models
from cli_tool_audit.models import CliToolConfig


@given(
    name=st.text(),
    version=st.one_of(st.none(), st.text()),
    version_switch=st.one_of(st.none(), st.text()),
    schema=st.one_of(st.none(), st.sampled_from(cli_tool_audit.models.SchemaType)),
    if_os=st.one_of(st.none(), st.text()),
    tags=st.one_of(st.none(), st.lists(st.text())),
    install_command=st.one_of(st.none(), st.text()),
    install_docs=st.one_of(st.none(), st.text()),
)
def test_fuzz_CliToolConfig(
    name: str,
    version: str | None,
    version_switch: str | None,
    schema: cli_tool_audit.models.SchemaType | None,
    if_os: str | None,
    tags: list[str] | None,
    install_command: str | None,
    install_docs: str | None,
) -> None:
    cli_tool_audit.models.CliToolConfig(
        name=name,
        version=version,
        version_switch=version_switch,
        schema=schema,
        if_os=if_os,
        tags=tags,
        install_command=install_command,
        install_docs=install_docs,
    )


@given(
    is_available=st.booleans(),
    is_broken=st.booleans(),
    version=st.one_of(st.none(), st.text()),
    last_modified=st.one_of(st.none(), st.datetimes()),
)
def test_fuzz_ToolAvailabilityResult(
    is_available: bool,
    is_broken: bool,
    version: str | None,
    last_modified: datetime.datetime | None,
) -> None:
    cli_tool_audit.models.ToolAvailabilityResult(
        is_available=is_available,
        is_broken=is_broken,
        version=version,
        last_modified=last_modified,
    )


@given(
    tool=st.text(),
    desired_version=st.text(),
    is_needed_for_os=st.booleans(),
    is_available=st.booleans(),
    is_snapshot=st.booleans(),
    found_version=st.one_of(st.none(), st.text()),
    parsed_version=st.one_of(st.none(), st.text()),
    is_compatible=st.text(),
    is_broken=st.booleans(),
    last_modified=st.one_of(st.none(), st.datetimes()),
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
def test_fuzz_ToolCheckResult(
    tool: str,
    desired_version: str,
    is_needed_for_os: bool,
    is_available: bool,
    is_snapshot: bool,
    found_version: str | None,
    parsed_version: str | None,
    is_compatible: str,
    is_broken: bool,
    last_modified: datetime.datetime | None,
    tool_config: cli_tool_audit.models.CliToolConfig,
) -> None:
    cli_tool_audit.models.ToolCheckResult(
        tool=tool,
        desired_version=desired_version,
        is_needed_for_os=is_needed_for_os,
        is_available=is_available,
        is_snapshot=is_snapshot,
        found_version=found_version,
        parsed_version=parsed_version,
        is_compatible=is_compatible,
        is_broken=is_broken,
        last_modified=last_modified,
        tool_config=tool_config,
    )
