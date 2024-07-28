from cli_tool_audit.compatibility import check_compatibility
from cli_tool_audit.compatibility import split_version_match_pattern, check_compatibility
from unittest.mock import patch, ANY
import pytest





# ### Bug Report:
# 
# 1. In the `split_version_match_pattern` function, the `match_pattern_regex`
#    should have a caret `^` at the beginning to match from the start of the
#    string. The corrected regex should be `r"^(>=|<=|!=|>|<|==|~=|~)?(.*)"` to
#    ensure accurate matching.
# 
# ### Unit Test:
# 
# I will write pytest unit tests to cover the different scenarios of the
# `compatibility.py` module. I will use `pytest` along with `unittest.mock` for
# mocking.

# Unit test for split_version_match_pattern function
def test_split_version_match_pattern():
    assert split_version_match_pattern(">=1.1.1") == (">=", "1.1.1")
    assert split_version_match_pattern("1.1.1") == ("", "1.1.1")
    assert split_version_match_pattern("==1.1.1") == ("==", "1.1.1")
    assert split_version_match_pattern("~=1.1.1") == ("~=", "1.1.1")

# Unit test for check_compatibility function
@patch('cli_tool_audit.compatibility.logger')
@patch('cli_tool_audit.compatibility.split_version_match_pattern')
@patch('cli_tool_audit.compatibility.version_parsing.two_pass_semver_parse')
@patch('cli_tool_audit.compatibility.compatibility_complex.check_range_compatibility')
def test_check_compatibility(mock_check_range_compatibility, mock_two_pass_semver_parse, mock_split_version_match_pattern, mock_logger):

    # Case where found_version is None
    mock_split_version_match_pattern.return_value = ("==", "1.1.1")
    assert check_compatibility("==1.1.1", None) == ("Can't tell", None)

