"""Extended tests for cli_tool_audit.models module."""

import datetime

import pytest

from cli_tool_audit.models import CliToolConfig, SchemaType, ToolAvailabilityResult, ToolCheckResult


def _base_result(**overrides) -> ToolCheckResult:
    defaults = dict(
        tool="mytool",
        desired_version="1.0.0",
        is_needed_for_os=True,
        is_available=True,
        is_snapshot=False,
        found_version="1.0.0",
        parsed_version="1.0.0",
        is_compatible="Compatible",
        is_broken=False,
        last_modified=None,
        tool_config=CliToolConfig(name="mytool", schema=SchemaType.SEMVER),
    )
    defaults.update(overrides)
    return ToolCheckResult(**defaults)


# ---------------------------------------------------------------------------
# SchemaType
# ---------------------------------------------------------------------------


class TestSchemaType:
    def test_str_returns_value(self):
        assert str(SchemaType.SEMVER) == "semver"
        assert str(SchemaType.SNAPSHOT) == "snapshot"
        assert str(SchemaType.EXISTENCE) == "existence"
        assert str(SchemaType.PEP440) == "pep440"

    def test_from_value(self):
        assert SchemaType("semver") == SchemaType.SEMVER
        assert SchemaType("existence") == SchemaType.EXISTENCE

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            SchemaType("invalid")


# ---------------------------------------------------------------------------
# CliToolConfig.cache_hash
# ---------------------------------------------------------------------------


class TestCliToolConfigCacheHash:
    def test_same_config_same_hash(self):
        a = CliToolConfig(name="tool", version="1.0.0")
        b = CliToolConfig(name="tool", version="1.0.0")
        assert a.cache_hash() == b.cache_hash()

    def test_different_name_different_hash(self):
        a = CliToolConfig(name="tool_a")
        b = CliToolConfig(name="tool_b")
        assert a.cache_hash() != b.cache_hash()

    def test_different_version_different_hash(self):
        a = CliToolConfig(name="tool", version="1.0.0")
        b = CliToolConfig(name="tool", version="2.0.0")
        assert a.cache_hash() != b.cache_hash()

    def test_hash_is_string(self):
        config = CliToolConfig(name="tool")
        assert isinstance(config.cache_hash(), str)

    def test_hash_length_is_md5(self):
        config = CliToolConfig(name="tool")
        assert len(config.cache_hash()) == 32


# ---------------------------------------------------------------------------
# ToolCheckResult.failure_reason
# ---------------------------------------------------------------------------


class TestFailureReason:
    def test_wrong_os(self):
        result = _base_result(is_needed_for_os=False)
        assert result.failure_reason() == "wrong os"

    def test_not_found(self):
        result = _base_result(is_available=False)
        assert result.failure_reason() == "not found"

    def test_available_existence_schema(self):
        result = _base_result(
            tool_config=CliToolConfig(name="mytool", schema=SchemaType.EXISTENCE),
            is_compatible="Compatible",
        )
        assert result.failure_reason() == "available"

    def test_broken(self):
        result = _base_result(is_broken=True, is_compatible="Can't tell")
        assert result.failure_reason() == "broken"

    def test_compatible(self):
        result = _base_result(is_compatible="Compatible")
        assert result.failure_reason() == "compatible"

    def test_cant_tell(self):
        result = _base_result(is_compatible="Can't tell")
        assert result.failure_reason() == "unknown version"

    def test_not_found_string(self):
        result = _base_result(is_compatible="Not Found")
        assert result.failure_reason() == "not found"

    def test_different_version(self):
        result = _base_result(is_compatible="different")
        assert result.failure_reason() == "different version"

    def test_outdated(self):
        result = _base_result(is_compatible=">=2.0.0 != 1.0.0")
        reason = result.failure_reason()
        assert "outdated" in reason
        assert "1.0.0" in reason
        assert ">=2.0.0" in reason

    def test_other_compat_string_lowercased(self):
        result = _base_result(is_compatible="SomeOtherReason")
        assert result.failure_reason() == "someotherreason"


# ---------------------------------------------------------------------------
# ToolCheckResult.status
# ---------------------------------------------------------------------------


class TestStatus:
    def test_wrong_os(self):
        result = _base_result(is_needed_for_os=False)
        assert result.status() == "Wrong OS"

    def test_not_found(self):
        result = _base_result(is_available=False)
        assert result.status() == "Not found"

    def test_available_existence(self):
        result = _base_result(tool_config=CliToolConfig(name="mytool", schema=SchemaType.EXISTENCE))
        assert result.status() == "Available"

    def test_broken(self):
        result = _base_result(is_broken=True, is_compatible="Can't tell")
        assert result.status() == "Broken (version check failed)"

    def test_compatible(self):
        result = _base_result()
        assert result.status() == "Compatible"

    def test_unknown_version(self):
        result = _base_result(is_compatible="Can't tell")
        assert result.status() == "Unknown version"

    def test_different_version(self):
        result = _base_result(is_compatible="different")
        assert result.status() == "Different version"

    def test_outdated_status_is_capitalized(self):
        result = _base_result(is_compatible=">=2.0.0 != 1.0.0")
        status = result.status()
        assert status[0].isupper()


# ---------------------------------------------------------------------------
# ToolCheckResult.is_problem
# ---------------------------------------------------------------------------


class TestIsProblem:
    def test_compatible_and_available_is_not_problem(self):
        result = _base_result()
        assert result.is_problem() is False

    def test_unavailable_is_problem(self):
        result = _base_result(is_available=False)
        assert result.is_problem() is True

    def test_incompatible_is_problem(self):
        result = _base_result(is_compatible=">=2.0.0 != 1.0.0")
        assert result.is_problem() is True

    def test_wrong_os_not_a_problem(self):
        result = _base_result(is_needed_for_os=False, is_available=False, is_compatible="wrong os")
        assert result.is_problem() is False

    def test_broken_but_available_and_compatible_is_still_not_problem_by_field(self):
        # is_problem only checks is_compatible and is_available, not is_broken
        result = _base_result(is_broken=True, is_available=True, is_compatible="Compatible")
        assert result.is_problem() is False


# ---------------------------------------------------------------------------
# ToolAvailabilityResult
# ---------------------------------------------------------------------------


class TestToolAvailabilityResult:
    def test_fields(self):
        result = ToolAvailabilityResult(
            is_available=True,
            is_broken=False,
            version="1.2.3",
            last_modified=datetime.datetime(2024, 1, 1),
        )
        assert result.is_available is True
        assert result.is_broken is False
        assert result.version == "1.2.3"
        assert result.last_modified == datetime.datetime(2024, 1, 1)
