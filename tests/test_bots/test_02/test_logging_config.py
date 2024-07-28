from cli_tool_audit.logging_config import generate_config
from types import MappingProxyType
from unittest.mock import patch
import os





# ### Issues in the code:
# 
# 1. In the `generate_config` function, the type hint for the return value should
#    use `mappingproxy` instead of `dict`.

# def generate_config(level: str = "DEBUG") -> MappingProxyType[str, Any]:

# ### Proposed unit tests:
# 
# I will write unit tests to cover the following scenarios:
# 
# 1. Test the logging configuration when the environment variable "NO_COLOR" is
#    set.
# 2. Test the logging configuration when the environment variable "CI" is set.
# 3. Test the logging configuration when neither "NO_COLOR" nor "CI" environment
#    variables are set.
# 4. Test the default logging configuration.

def test_generate_config_no_color_set():
    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        config = generate_config()
    assert config["handlers"]["default"]["formatter"] == "standard"

def test_generate_config_ci_set():
    with patch.dict(os.environ, {"CI": "1"}):
        config = generate_config()
    assert config["handlers"]["default"]["formatter"] == "standard"

def test_generate_config_no_env_set():
    with patch.dict(os.environ, clear=True):
        config = generate_config()
    assert config["handlers"]["default"]["formatter"] == "colored"

def test_generate_config_default():
    config = generate_config()
    assert config["handlers"]["default"]["formatter"] == "colored"
    
def test_generate_config_return_type():
    config = generate_config()
    assert isinstance(config, dict)

# No more unit tests

# These tests will cover the different scenarios based on the environment
# variables and the default logging configuration.
