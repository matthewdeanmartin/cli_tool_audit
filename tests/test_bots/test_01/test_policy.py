from unittest.mock import MagicMock

import pytest

from cli_tool_audit.models import ToolCheckResult
from cli_tool_audit.policy import apply_policy


@pytest.mark.parametrize(
    "tool_results, expected",
    [
        (
            [
                MagicMock(is_broken=False, is_available=True, is_compatible=True),
                MagicMock(is_broken=False, is_available=True, is_compatible=True),
                MagicMock(is_broken=False, is_available=True, is_compatible=True),
            ],
            False,
        ),  # All tools are valid
        (
            [
                MagicMock(is_broken=True, is_available=True, is_compatible=True),
                MagicMock(is_broken=False, is_available=True, is_compatible=True),
                MagicMock(is_broken=False, is_available=True, is_compatible=True),
            ],
            True,
        ),  # One tool is broken
        (
            [
                MagicMock(is_broken=False, is_available=False, is_compatible=True),
                MagicMock(is_broken=False, is_available=True, is_compatible=True),
                MagicMock(is_broken=False, is_available=True, is_compatible=True),
            ],
            True,
        ),  # One tool is not available
        (
            [
                MagicMock(is_broken=False, is_available=True, is_compatible=False),
                MagicMock(is_broken=False, is_available=True, is_compatible=True),
                MagicMock(is_broken=False, is_available=True, is_compatible=True),
            ],
            True,
        ),  # One tool is incompatible
        (
            [
                MagicMock(is_broken=False, is_available=False, is_compatible=False),
                MagicMock(is_broken=False, is_available=False, is_compatible=False),
            ],
            True,
        ),  # All tools are invalid
    ],
)
def test_apply_policy(tool_results, expected):
    result = apply_policy(tool_results)
    assert result == expected


def test_apply_policy_happy_path():
    # Creating mock ToolCheckResults that are all valid
    tool_ok_1 = MagicMock(spec=ToolCheckResult)
    tool_ok_1.is_broken = False
    tool_ok_1.is_available = True
    tool_ok_1.is_compatible = True

    tool_ok_2 = MagicMock(spec=ToolCheckResult)
    tool_ok_2.is_broken = False
    tool_ok_2.is_available = True
    tool_ok_2.is_compatible = True

    results = [tool_ok_1, tool_ok_2]

    assert apply_policy(results) is False


def test_apply_policy_mixed_results():
    # Testing mixed valid and invalid ToolCheckResults
    tool_ok = MagicMock(spec=ToolCheckResult)
    tool_ok.is_broken = False
    tool_ok.is_available = True
    tool_ok.is_compatible = True

    tool_fail_broken = MagicMock(spec=ToolCheckResult)
    tool_fail_broken.is_broken = True
    tool_fail_broken.is_available = True
    tool_fail_broken.is_compatible = True

    tool_fail_incompatible = MagicMock(spec=ToolCheckResult)
    tool_fail_incompatible.is_broken = False
    tool_fail_incompatible.is_available = True
    tool_fail_incompatible.is_compatible = False

    results = [tool_ok, tool_fail_broken, tool_fail_incompatible]

    assert apply_policy(results) is True


def test_apply_policy_empty_list():
    # Edge case testing an empty list
    results = []

    assert apply_policy(results) is False


def test_apply_policy_unexpected_attribute():
    # Testing when an attribute is missing
    missing_attr_tool = MagicMock(spec=ToolCheckResult)
    missing_attr_tool.is_broken = False
    missing_attr_tool.is_available = True
    del missing_attr_tool.is_compatible  # Simulate missing attribute

    with pytest.raises(AttributeError):
        apply_policy([missing_attr_tool])
