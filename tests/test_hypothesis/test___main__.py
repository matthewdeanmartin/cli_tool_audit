# # This test code was written by the `hypothesis.extra.ghostwriter` module
# # and is provided under the Creative Commons Zero public domain dedication.
#
# import argparse
# import cli_tool_audit.__main__
# import collections.abc
# import typing
# from argparse import ArgumentParser, Namespace
# from hypothesis import given, strategies as st
#
# # TODO: replace st.nothing() with appropriate strategies
#
#
# @given(interactive_parser=st.nothing())
# def test_fuzz_add_config_to_subparser(interactive_parser) -> None:
#     cli_tool_audit.add_config_to_subparser(interactive_parser=interactive_parser)
#
#
# @given(audit_parser=st.nothing())
# def test_fuzz_add_formats(audit_parser) -> None:
#     cli_tool_audit.add_formats(audit_parser=audit_parser)
#
#
# @given(parser=st.nothing())
# def test_fuzz_add_schema_argument(parser) -> None:
#     cli_tool_audit.add_schema_argument(parser=parser)
#
#
# @given(parser=st.from_type(argparse.ArgumentParser))
# def test_fuzz_add_update_args(parser: argparse.ArgumentParser) -> None:
#     cli_tool_audit.add_update_args(parser=parser)
#
#
# @given(args=st.from_type(argparse.Namespace))
# def test_fuzz_handle_audit(args: argparse.Namespace) -> None:
#     cli_tool_audit.handle_audit(args=args)
#
#
# @given(args=st.from_type(argparse.Namespace))
# def test_fuzz_handle_create(args: argparse.Namespace) -> None:
#     cli_tool_audit.handle_create(args=args)
#
#
# @given(args=st.from_type(argparse.Namespace))
# def test_fuzz_handle_delete(args: argparse.Namespace) -> None:
#     cli_tool_audit.handle_delete(args=args)
#
#
# @given(args=st.from_type(argparse.Namespace))
# def test_fuzz_handle_interactive(args: argparse.Namespace) -> None:
#     cli_tool_audit.handle_interactive(args=args)
#
#
# @given(args=st.from_type(argparse.Namespace))
# def test_fuzz_handle_read(args: argparse.Namespace) -> None:
#     cli_tool_audit.handle_read(args=args)
#
#
# @given(args=st.nothing())
# def test_fuzz_handle_single(args) -> None:
#     cli_tool_audit.handle_single(args=args)
#
#
# @given(args=st.from_type(argparse.Namespace))
# def test_fuzz_handle_update(args: argparse.Namespace) -> None:
#     cli_tool_audit.handle_update(args=args)
#
#
# @given(argv=st.one_of(st.none(), st.lists(st.text())))
# def test_fuzz_main(argv: typing.Optional[collections.abc.Sequence[str]]) -> None:
#     cli_tool_audit.main(argv=argv)
#
#
# @given(args=st.from_type(argparse.Namespace))
# def test_fuzz_reduce_args_tool_cli_tool_config_args(args: argparse.Namespace) -> None:
#     cli_tool_audit.reduce_args_tool_cli_tool_config_args(args=args)
#
