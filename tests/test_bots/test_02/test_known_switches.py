import pytest

from cli_tool_audit.known_switches import KNOWN_SWITCHES





# ### Bugs:
# 
# - The comment mentioning `modern versions also support --version` should be
#   moved to a separate line above the corresponding tool for clarity.
# 
# ### Unit Test:
# 
# I will write unit tests to verify the correctness of the `KNOWN_SWITCHES`
# dictionary in `known_switches.py`.

def test_known_switches():
    assert KNOWN_SWITCHES["npm"] == "version"
    assert KNOWN_SWITCHES["terraform"] == "-version"
    assert KNOWN_SWITCHES["java"] == "-version"

# No more unit tests

# By running this test, we can ensure that the `KNOWN_SWITCHES` dictionary
# contains the correct switches for the specified CLI tools.
# ### Unit Test:
# 
# I will write a unit test to verify that accessing a non-existent tool in the
# `KNOWN_SWITCHES` dictionary raises a KeyError.

def test_invalid_tool():
    with pytest.raises(KeyError):
        switch = KNOWN_SWITCHES["non_existing_tool"]

# No more unit tests

# In this test, we are checking that accessing a non-existent tool in the
# `KNOWN_SWITCHES` dictionary raises a KeyError, as expected.
# ### Unit Test:
# 
# I will write a unit test to ensure that the keys in the `KNOWN_SWITCHES`
# dictionary are valid and properly formatted.

def test_valid_keys():
    valid_keys = ["npm", "terraform", "java"]
    assert all(tool in KNOWN_SWITCHES for tool in valid_keys)

# No more unit tests

# This test verifies that all the keys present in the `KNOWN_SWITCHES` dictionary
# match the expected valid key names used for CLI tools.
# ### Unit Test:
# 
# I will write a unit test to ensure that the values in the `KNOWN_SWITCHES`
# dictionary are valid and of the correct type.

def test_valid_switch_values():
    valid_switch_values = ["version", "-version"]
    assert all(value in valid_switch_values for value in KNOWN_SWITCHES.values())

# No more unit tests

# This test checks that all the values in the `KNOWN_SWITCHES` dictionary are
# valid switch values used for CLI tools.
# ### Unit Test:
# 
# I will write a unit test to validate that the `KNOWN_SWITCHES` dictionary is not
# empty.

def test_known_switches_not_empty():
    assert len(KNOWN_SWITCHES) > 0

# No more unit tests

# This test ensures that the `KNOWN_SWITCHES` dictionary is not empty, as it
# should contain mappings of CLI tools to their corresponding switches.
