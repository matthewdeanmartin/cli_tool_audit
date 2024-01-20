# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

import typing
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

import cli_tool_audit.models
import cli_tool_audit.views
from cli_tool_audit.models import CliToolConfig, ToolCheckResult


@given(
    results=st.lists(
        st.builds(
            ToolCheckResult,
            desired_version=st.sampled_from(["0.1.2", "2.3.4", "*", ">1.2.3"]),
            found_version=st.one_of(st.none(), st.sampled_from(["0.1.2", "2.3.4", "1.2.3"])),
            is_available=st.booleans(),
            is_broken=st.booleans(),
            is_compatible=st.text(),
            is_needed_for_os=st.booleans(),
            is_snapshot=st.booleans(),
            last_modified=st.one_of(st.none(), st.datetimes()),
            parsed_version=st.one_of(st.none(), st.sampled_from(["0.1.2", "2.3.4", "1.2.3"])),
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
                version=st.one_of(st.none(), st.one_of(st.none(), st.sampled_from(["0.1.2", "2.3.4", "1.2.3"]))),
                version_switch=st.one_of(st.none(), st.one_of(st.none(), st.sampled_from(["--verion", "-v"]))),
            ),
        )
    ),
    truncate_long_versions=st.booleans(),
    include_docs=st.booleans(),
)
def test_fuzz_pretty_print_results(
    results: list[cli_tool_audit.models.ToolCheckResult],
    truncate_long_versions: bool,
    include_docs: bool,
) -> None:
    cli_tool_audit.views.pretty_print_results(
        results=results,
        truncate_long_versions=truncate_long_versions,
        include_docs=include_docs,
    )


# Slow!
# @given(
#     cli_tools=st.dictionaries(
#         keys=st.text(),
#         values=st.builds(
#             CliToolConfig,
#             if_os=st.one_of(st.none(), st.one_of(st.none(), st.text())),
#             install_command=st.one_of(st.none(), st.one_of(st.none(), st.text())),
#             install_docs=st.one_of(st.none(), st.one_of(st.none(), st.text())),
#             name=st.text(),
#             schema=st.one_of(
#                 st.none(),
#                 st.one_of(st.none(), st.sampled_from(cli_tool_audit.models.SchemaType)),
#             ),
#             tags=st.one_of(st.none(), st.one_of(st.none(), st.lists(st.text()))),
#             version=st.one_of(st.none(), st.one_of(st.none(), st.text())),
#             version_switch=st.one_of(st.none(), st.one_of(st.none(), st.text())),
#         ),
#     ),
#     no_cache=st.booleans(),
#     tags=st.one_of(st.none(), st.lists(st.text())),
#     disable_progress_bar=st.booleans(),
# )
# def test_fuzz_process_tools(
#     cli_tools: dict[str, cli_tool_audit.models.CliToolConfig],
#     no_cache: bool,
#     tags: typing.Optional[list[str]],
#     disable_progress_bar: bool,
# ) -> None:
#     cli_tool_audit.views.process_tools(
#         cli_tools=cli_tools,
#         no_cache=no_cache,
#         tags=tags,
#         disable_progress_bar=disable_progress_bar,
#     )

# Hangs
# @given(
#     file_path=st.one_of(st.none(), st.sampled_from([Path("."), Path("audit.toml")])),
#     config_as_dict=st.one_of(
#         st.none(),
#         st.dictionaries(
#             keys=st.text(),
#             values=st.builds(
#                 CliToolConfig,
#                 if_os=st.one_of(st.none(), st.one_of(st.none(), st.text())),
#                 install_command=st.one_of(st.none(), st.one_of(st.none(), st.text())),
#                 install_docs=st.one_of(st.none(), st.one_of(st.none(), st.text())),
#                 name=st.sampled_from(["python", "pip"]),
#                 schema=st.one_of(
#                     st.none(),
#                     st.one_of(
#                         st.none(), st.sampled_from(cli_tool_audit.models.SchemaType)
#                     ),
#                 ),
#                 tags=st.one_of(st.none(), st.one_of(st.none(), st.lists(st.text()))),
#                 version=st.one_of(st.none(), st.one_of(st.none(), st.sampled_from(["0.1.2", "2.3.4", "1.2.3"]))),
#                 version_switch=st.one_of(st.none(), st.one_of(st.none(), st.sampled_from(["--verion", "-v"]))),
#             ),
#         ),
#     ),
#     exit_code_on_failure=st.booleans(),
#     file_format=st.sampled_from(["toml", "json", "yaml", "xml", "html", "csv","json-lines","table"]),
#     no_cache=st.booleans(),
#     tags=st.one_of(st.none(), st.lists(st.text())),
#     only_errors=st.booleans(),
# )
# @settings(suppress_health_check=[HealthCheck.too_slow])
# def test_fuzz_report_from_pyproject_toml(
#     file_path: typing.Optional[Path],
#     config_as_dict: typing.Optional[dict[str, cli_tool_audit.models.CliToolConfig]],
#     exit_code_on_failure: bool,
#     file_format: str,
#     no_cache: bool,
#     tags: typing.Optional[list[str]],
#     only_errors: bool,
# ) -> None:
#     if file_path is not None and config_as_dict is not None:
#         cli_tool_audit.views.report_from_pyproject_toml(
#             file_path=file_path,
#             config_as_dict=config_as_dict,
#             exit_code_on_failure=exit_code_on_failure,
#             file_format=file_format,
#             no_cache=no_cache,
#             tags=tags,
#             only_errors=only_errors,
#         )


@given(
    file_path=st.sampled_from([Path("."), Path("../pyproject.toml"), Path("audit.toml")]),
    no_cache=st.booleans(),
    tags=st.one_of(st.none(), st.lists(st.text())),
    disable_progress_bar=st.booleans(),
)
def test_fuzz_validate(
    file_path: Path,
    no_cache: bool,
    tags: typing.Optional[list[str]],
    disable_progress_bar: bool,
) -> None:
    cli_tool_audit.views.validate(
        file_path=file_path,
        no_cache=no_cache,
        tags=tags,
        disable_progress_bar=disable_progress_bar,
    )
