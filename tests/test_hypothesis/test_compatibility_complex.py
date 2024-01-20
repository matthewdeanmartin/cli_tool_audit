# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import cli_tool_audit.compatibility_complex

#
# @given(
#     desired_version=st.text(),
#     found_semversion=st.builds(
#         Version,
#         build=st.one_of(
#             st.none(), st.one_of(st.none(), st.integers(), st.binary(), st.text())
#         ),
#         major=st.one_of(
#             st.booleans(),
#             st.integers(),
#             st.floats(),
#             st.uuids(),
#             st.decimals(),
#             st.from_regex("\\A-?\\d+\\Z").filter(functools.partial(can_cast, int)),
#         ),
#         minor=st.one_of(
#             st.just(0),
#             st.one_of(
#                 st.booleans(),
#                 st.integers(),
#                 st.floats(),
#                 st.uuids(),
#                 st.decimals(),
#                 st.from_regex("\\A-?\\d+\\Z").filter(functools.partial(can_cast, int)),
#             ),
#         ),
#         patch=st.one_of(
#             st.just(0),
#             st.one_of(
#                 st.booleans(),
#                 st.integers(),
#                 st.floats(),
#                 st.uuids(),
#                 st.decimals(),
#                 st.from_regex("\\A-?\\d+\\Z").filter(functools.partial(can_cast, int)),
#             ),
#         ),
#         prerelease=st.one_of(
#             st.none(), st.one_of(st.none(), st.integers(), st.binary(), st.text())
#         ),
#     ),
# )
# def test_fuzz_check_range_compatibility(
#     desired_version: str, found_semversion: semver.Version
# ) -> None:
#     cli_tool_audit.compatibility_complex.check_range_compatibility(
#         desired_version=desired_version, found_semversion=found_semversion
#     )


@given(version_range=st.sampled_from(["^0.1.2", "~2.3.4", "*"]))
def test_fuzz_convert_version_range(version_range: str) -> None:
    cli_tool_audit.compatibility_complex.convert_version_range(version_range=version_range)
