import pytest

from cli_tool_audit.config_manager import ConfigManager

# Sample data for testing
SAMPLE_TOOL_CONFIG = {
    "foobar": {"version": ">=1.0.0"},
    "foo": {"version": ">=1.0.0", "version_switch": "version"},
    # Add more sample configurations as needed
}


@pytest.fixture
def config_file(tmp_path):
    config = tmp_path / "config.toml"
    with config.open("w") as f:
        # Write initial configuration for testing
        f.write("[tool.cli-tools]\n")
        for tool, settings in SAMPLE_TOOL_CONFIG.items():
            f.write(f"{tool} = {str(settings).replace(':','=')}\n")
    return config


def test_read_config(config_file):
    config_manager = ConfigManager(str(config_file))
    config_manager.read_config()
    assert config_manager.tools["foobar"].version == ">=1.0.0"
    assert config_manager.tools["foo"].version_switch == "version"
    # Add more assertions as needed


def test_create_tool_config(config_file):
    config_manager = ConfigManager(str(config_file))
    config_manager.create_tool_config("newtool", {"version": ">=2.0.0"})
    assert "newtool" in config_manager.tools
    assert config_manager.tools["newtool"].version == ">=2.0.0"


def test_update_tool_config(config_file):
    config_manager = ConfigManager(str(config_file))
    # config_manager.read_config()
    config_manager.update_tool_config("foobar", {"version": ">=1.1.0"})
    assert config_manager.tools["foobar"].version == ">=1.1.0"


def test_delete_tool_config(config_file):
    config_manager = ConfigManager(str(config_file))
    # config_manager.read_config()
    config_manager.delete_tool_config("foobar")
    assert "foobar" not in config_manager.tools
