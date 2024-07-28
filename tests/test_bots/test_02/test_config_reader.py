from cli_tool_audit import config_reader
from cli_tool_audit.models import CliToolConfig
from pathlib import Path
from unittest.mock import MagicMock, patch
import logging
import pytest





# ### Bug Report:
# 
# 1. In the `read_config` function of `config_reader.py`, the `print` statement is
#    used to log the error when reading the pyproject.toml file. This is not ideal
#    as it bypasses the logging configuration and directly writes to stdout. It
#    would be better to log this error using the `logger.error` method to maintain
#    consistency with the rest of the logging in the module.
# 
# ### Unit Tests:
# 
# 1. Test the case where the `ConfigManager` successfully reads the config from
#    the file and returns the tools dictionary.
# 2. Test the case where the config section `[tool.cli-tools]` is not found in the
#    pyproject.toml file, and a warning is logged.
# 3. Test the case where an exception is raised during the config reading process,
#    ensure that the exception is logged and an empty dictionary is returned.
# 4. Test the case where the `ConfigManager` raises a `ValueError` while creating
#    a new tool config and verify that the error is handled properly.
# 5. Test the case where the `ConfigManager` raises a `ValueError` while updating
#    an existing tool config and verify that the error is handled appropriately.
# 6. Test the case where the `ConfigManager` successfully creates or updates a
#    tool config.
# 7. Test the case where the `ConfigManager` successfully deletes an existing tool
#    config.
# 8. Test the case where the save operation of the `ConfigManager` is invoked and
#    ensure that it behaves as expected.
# 
# ### Unit Tests Code:


@pytest.fixture
def mock_config_manager(monkeypatch):
    mock_manager = MagicMock()
    mock_manager.read_config.return_value = True
    mock_manager.tools = {'tool1': CliToolConfig(name="name"), 'tool2': CliToolConfig(name="name2")}
    monkeypatch.setattr(config_reader.config_manager, "ConfigManager", MagicMock(return_value=mock_manager))
    return mock_manager

def test_read_config_existing_section(mock_config_manager):
    file_path = Path("test.toml")
    
    result = config_reader.read_config(file_path)
    
    assert result == mock_config_manager.tools
    mock_config_manager.read_config.assert_called_once()
    mock_config_manager.read_config.assert_called_with()
