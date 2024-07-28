from cli_tool_audit.audit_manager import AuditManager
from cli_tool_audit.models import CliToolConfig, SchemaType
import pytest





# ### Bugs:
# 
# 1. In the `call_tool` method of `AuditManager`, the handling of schema types
#    other than `EXISTENCE` is not consistent. The `if` block is written for
#    `EXISTENCE` type, but the subsequent `elif` blocks are using string literals
#    like `"SNAPSHOT"`, `"pep440"` without checking against the actual
#    `SchemaType` class instances.
# 
# ### Unit Tests:

@pytest.fixture
def mock_tool_config():
    return CliToolConfig(name="test_tool", schema=SchemaType.SEMVER, version="1.2.3", if_os="linux")


# Add more test cases for other schema types

def test_when_tool_not_found_for_given_os(mocker, mock_tool_config):
    with mocker.patch('cli_tool_audit.audit_manager.which', return_value=None):
        audit_manager = AuditManager()
        result = audit_manager.call_and_check(mock_tool_config)
        assert not result.is_available
        assert not result.is_needed_for_os
        assert result.is_broken is False

