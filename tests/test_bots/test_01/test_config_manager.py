from pathlib import Path
from unittest.mock import patch

import pytest
import toml

from cli_tool_audit import models
from cli_tool_audit.config_manager import ConfigManager


def test_read_config_file_not_found(tmp_path):
    # Create an instance of ConfigManager with a path that does not exist
    config_path = tmp_path / "non_existent_config.toml"
    config_manager = ConfigManager(config_path)

    # Mock Path.exists to return False
    with patch.object(Path, "exists", return_value=False):
        result = config_manager.read_config()

    # Assert that the method returns False when the file doesn't exist
    assert result is False
    assert len(config_manager.tools) == 0


@pytest.fixture
def mock_toml_load():
    """Fixture to mock toml.load return value."""
    return {
        "tool": {
            "cli-tools": {
                "my_tool": {
                    "version_snapshot": "1.0.0",
                },
                "another_tool": {
                    "only_check_existence": True,
                },
            }
        }
    }


def test_read_config_happy_path(tmp_path, mock_toml_load):
    # Create a mock TOML configuration file
    config_path = tmp_path / "config.toml"
    config_path.write_text(toml.dumps(mock_toml_load), encoding="utf-8")

    # Create an instance of ConfigManager
    config_manager = ConfigManager(config_path)

    # Mock Path.exists to return True and toml.load to return mock data
    with (
        patch.object(Path, "exists", return_value=True),
        patch("cli_tool_audit.config_manager.toml.load", return_value=mock_toml_load),
    ):

        result = config_manager.read_config()

    # Assert that the method returns True and tools are populated correctly
    assert result is True
    assert len(config_manager.tools) == 2  # Two tools defined in the TOML
    assert "my_tool" in config_manager.tools
    assert "another_tool" in config_manager.tools
    assert config_manager.tools["my_tool"].version == "1.0.0"
    assert config_manager.tools["another_tool"].schema == models.SchemaType.EXISTENCE


def test_create_tool_config_existing_tool(tmp_path):
    # Create a mock configuration file with one tool
    initial_config = {
        "tool": {
            "cli-tools": {
                "existing_tool": {
                    "version": "1.0.0",
                }
            }
        }
    }
    config_path = tmp_path / "config.toml"
    config_path.write_text(toml.dumps(initial_config), encoding="utf-8")

    # Create an instance of ConfigManager
    config_manager = ConfigManager(config_path)
    config_manager.read_config()

    # Define a new tool configuration
    new_tool_config = {
        "version": "2.0.0",
    }

    # Attempt to create a tool that already exists
    with pytest.raises(ValueError, match="Tool existing_tool already exists"):
        config_manager.create_tool_config("existing_tool", new_tool_config)


def test_update_tool_config_non_existent_tool(tmp_path):
    # Create a mock configuration file with one tool
    initial_config = {
        "tool": {
            "cli-tools": {
                "existing_tool": {
                    "version": "1.0.0",
                }
            }
        }
    }
    config_path = tmp_path / "config.toml"
    config_path.write_text(toml.dumps(initial_config), encoding="utf-8")

    # Create an instance of ConfigManager
    config_manager = ConfigManager(config_path)
    config_manager.read_config()

    # Define an updated tool configuration for a non-existent tool
    updated_tool_config = {
        "version": "2.0.0",
    }

    # Attempt to update a tool that does not exist
    with pytest.raises(ValueError, match="Tool non_existent_tool does not exist"):
        config_manager.update_tool_config("non_existent_tool", updated_tool_config)
