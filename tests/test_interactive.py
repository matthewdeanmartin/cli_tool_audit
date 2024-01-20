from unittest.mock import patch

from cli_tool_audit.config_manager import ConfigManager
from cli_tool_audit.interactive import interactive_config_manager


def test_interactive_config_manager(tmp_path):
    # Create a temporary config file
    config_path = tmp_path / "test_config.toml"
    config_path.write_text("")

    # Instantiate ConfigManager with the temporary config file path
    config_manager = ConfigManager(config_path)

    # Mock inputs for the interactive_config_manager function
    user_inputs = iter(
        [
            "1",  # Choose to create/update config
            "test_tool",  # Tool name
            "no",  # Check existence only? - No
            "snapshot",  # Schema
            # '',                  # Version - not required for snapshot
            "--version",  # Version switch
            "linux",  # OS-specific
            "3",  # Exit the interactive mode
        ]
    )

    with patch("builtins.input", lambda _: next(user_inputs)):
        interactive_config_manager(config_manager)

    # Read the config file to verify changes
    with open(config_path, encoding="utf-8") as file:
        config_data = file.read()

    # Asserts to validate if the config file was updated correctly
    assert "test_tool" in config_data
    assert "snapshot" in config_data
    assert "--version" in config_data
    assert "linux" in config_data
