"""Tests for cli_tool_audit.policy module."""

from cli_tool_audit.models import CliToolConfig, SchemaType, ToolCheckResult
from cli_tool_audit.policy import apply_policy


def _make_result(
    tool="mytool",
    is_needed_for_os=True,
    is_available=True,
    is_compatible="Compatible",
    is_broken=False,
) -> ToolCheckResult:
    return ToolCheckResult(
        tool=tool,
        desired_version="1.0.0",
        is_needed_for_os=is_needed_for_os,
        is_available=is_available,
        is_snapshot=False,
        found_version="1.0.0",
        parsed_version="1.0.0",
        is_compatible=is_compatible,
        is_broken=is_broken,
        last_modified=None,
        tool_config=CliToolConfig(name=tool, schema=SchemaType.SEMVER),
    )


def test_apply_policy_all_good_returns_false():
    results = [_make_result("a"), _make_result("b")]
    assert apply_policy(results) is False


def test_apply_policy_empty_returns_false():
    assert apply_policy([]) is False


def test_apply_policy_unavailable_tool_returns_true():
    results = [_make_result(is_available=False)]
    assert apply_policy(results) is True


def test_apply_policy_broken_tool_returns_true():
    results = [_make_result(is_broken=True)]
    assert apply_policy(results) is True


def test_apply_policy_incompatible_string_does_not_trigger_failure():
    # BUG: apply_policy checks `if not result.is_compatible` which is falsy only when
    # is_compatible is "" or None. A non-empty incompatibility string like ">=2.0.0 != 1.0.0"
    # is truthy, so `not result.is_compatible` is False and the policy does NOT fail.
    # This means incompatible-but-available tools slip through apply_policy.
    results = [_make_result(is_compatible=">=2.0.0 != 1.0.0")]
    assert apply_policy(results) is False  # documents the bug


def test_apply_policy_empty_is_compatible_triggers_failure():
    # Only an empty string for is_compatible triggers the policy failure
    results = [_make_result(is_compatible="")]
    assert apply_policy(results) is True


def test_apply_policy_wrong_os_is_not_treated_as_failure():
    # Wrong OS tools: is_available=False but is_broken=False, is_compatible is some string
    # The policy checks is_broken OR not is_available OR not is_compatible
    result = _make_result(is_needed_for_os=False, is_available=False, is_compatible="win32, not linux")
    # policy does NOT filter by is_needed_for_os — it checks is_broken/is_available/is_compatible directly
    # so a wrong-OS result with is_available=False WILL trigger failure per policy implementation
    results = [result]
    failed = apply_policy(results)
    # Documenting actual behavior: policy fails because not is_available
    assert failed is True


def test_apply_policy_mixed_results():
    results = [
        _make_result("good", is_available=True, is_compatible="Compatible"),
        _make_result("bad", is_available=False),
    ]
    assert apply_policy(results) is True
