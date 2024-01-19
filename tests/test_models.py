from cli_tool_audit.models import CliToolConfig, SchemaType, ToolCheckResult


def test_cache_hash():
    config = CliToolConfig(name="example_tool", version="1.0.0")
    config2 = CliToolConfig(name="example_tool", version="1.0.0")
    assert config.cache_hash() == config2.cache_hash()


def test_cache_hash_different():
    config = CliToolConfig(name="example_tool", version="1.0.0")
    config2 = CliToolConfig(name="example_tool", version="1.0.1")
    assert config.cache_hash() != config2.cache_hash()


def test_is_problem_no():
    result = ToolCheckResult(
        is_needed_for_os=True,
        tool="example_tool",
        desired_version="1.0.0",
        is_available=True,
        found_version="1.0.0",
        parsed_version="1.0.0",
        is_snapshot=False,
        is_compatible="Compatible",
        is_broken=False,
        last_modified=None,
        tool_config=CliToolConfig(
            name="test_tool",
            schema=SchemaType.SEMVER,
            version="0.0.0",
            version_switch="--version",
            if_os=None,
        ),
    )
    assert not result.is_problem()


def test_is_problem_yes():
    result = ToolCheckResult(
        is_needed_for_os=True,
        tool="example_tool",
        desired_version="1.0.0",
        is_available=False,
        found_version="1.0.0",
        parsed_version="1.0.0",
        is_snapshot=False,
        is_compatible="Compatible",
        is_broken=False,
        last_modified=None,
        tool_config=CliToolConfig(
            name="test_tool",
            schema=SchemaType.SEMVER,
            version="0.0.0",
            version_switch="--version",
            if_os=None,
        ),
    )
    assert result.is_problem()
