# # This test code was written by the `hypothesis.extra.ghostwriter` module
# # and is provided under the Creative Commons Zero public domain dedication.
#
# import cli_tool_audit.freeze
# import cli_tool_audit.models
# from hypothesis import given, strategies as st
#
#
# @given(
#     tool_names=st.lists(st.text()),
#     schema=st.sampled_from(cli_tool_audit.models.SchemaType),
# )
# def test_fuzz_freeze_requirements(
#     tool_names: list[str], schema: cli_tool_audit.models.SchemaType
# ) -> None:
#     cli_tool_audit.freeze.freeze_requirements(tool_names=tool_names, schema=schema)
#
#
# @given(
#     tool_names=st.lists(st.text()),
#     config_path=st.text(),
#     schema=st.sampled_from(cli_tool_audit.models.SchemaType),
# )
# def test_fuzz_freeze_to_config(
#     tool_names: list[str], config_path: str, schema: cli_tool_audit.models.SchemaType
# ) -> None:
#     cli_tool_audit.freeze.freeze_to_config(
#         tool_names=tool_names, config_path=config_path, schema=schema
#     )
#
#
# @given(
#     tool_names=st.lists(st.text()),
#     schema=st.sampled_from(cli_tool_audit.models.SchemaType),
# )
# def test_fuzz_freeze_to_screen(
#     tool_names: list[str], schema: cli_tool_audit.models.SchemaType
# ) -> None:
#     cli_tool_audit.freeze.freeze_to_screen(tool_names=tool_names, schema=schema)
#
