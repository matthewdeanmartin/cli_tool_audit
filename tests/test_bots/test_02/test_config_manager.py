from cli_tool_audit.config_manager import ConfigManager

# Let's start by identifying any issues in the `ConfigManager` class from
# `config_manager.py`:
#
# 1. In the `_save_config` method, the line
#    `with open(self.config_path, encoding="utf-8") as file:` should use
#    `str(self.config_path)` to open the file for writing.
# 2. In the `read_config` method, the line `if tool_name in self.tools:` should be
#    `if tool_name not in self.tools:` to check if the tool does not exist before
#    raising an error.
# 3. The `create_update_tool_config` method should correctly convert the schema
#    values to a string using `str(models.SchemaType(value))` when updating an
#    existing tool's config.
#
# Now, let's write pytest-style unit tests for the `ConfigManager` class:


def test_create_tool_config(tmp_path):
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    tool_name = "test_tool"
    tool_config = {"schema": "semver", "version": "2.0.0"}

    manager.create_tool_config(tool_name, tool_config)
    assert tool_name in manager.tools
    assert manager.tools[tool_name].schema == "semver"
    assert manager.tools[tool_name].version == "2.0.0"


def test_update_tool_config(tmp_path):
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    tool_name = "test_tool"
    tool_config = {"schema": "semver", "version": "2.0.0"}

    manager.create_tool_config(tool_name, tool_config)

    updated_tool_config = {"version": "3.0.0"}
    manager.update_tool_config(tool_name, updated_tool_config)

    assert manager.tools[tool_name].version == "3.0.0"


def test_create_update_tool_config(tmp_path):
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    tool_name = "test_tool"
    new_tool_config = {"schema": "semver", "version": "2.0.0"}
    manager.create_update_tool_config(tool_name, new_tool_config)
    assert manager.tools[tool_name].version == "2.0.0"

    updated_tool_config = {"version": "3.0.0"}
    manager.create_update_tool_config(tool_name, updated_tool_config)
    assert manager.tools[tool_name].version == "3.0.0"


def test_delete_tool_config(tmp_path):
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path)

    tool_name = "test_tool"
    tool_config = {"schema": "semver", "version": "2.0.0"}

    manager.create_tool_config(tool_name, tool_config)
    assert tool_name in manager.tools

    manager.delete_tool_config(tool_name)
    assert tool_name not in manager.tools
