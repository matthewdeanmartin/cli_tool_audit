from cli_tool_audit.models import CliToolConfig, SchemaType
from cli_tool_audit.models import CliToolConfig, SchemaType, ToolCheckResult
from cli_tool_audit.models import ToolAvailabilityResult
from cli_tool_audit.models import ToolCheckResult, CliToolConfig, SchemaType
from cli_tool_audit.models import ToolCheckResult, SchemaType
from datetime import datetime
from unittest.mock import Mock





# ### Bugs
# 
# 1. In `ToolCheckResult.status` method, the comparison
#    `self.tool_config.schema == "existence"` should be
#    `self.tool_config.schema == SchemaType.EXISTENCE`.
# 
# ### Unit Tests

def test_cache_hash():
    config = CliToolConfig(name="test", version="1.0", version_switch="--version", schema=SchemaType.SNAPSHOT, if_os="linux")
    
    expected_hash = "23c175298d521c1bb4014e916f0e1659"
    
    assert config.cache_hash() == expected_hash

def test_status_wrong_os():
    tool_result = ToolCheckResult(tool="test", desired_version="1.0", is_needed_for_os=False, is_available=True, is_snapshot=False, 
                                  found_version="1.0", parsed_version="1.0", is_compatible="Compatible", is_broken=False, 
                                  last_modified=None, tool_config=CliToolConfig(name="test", version="1.0", schema=SchemaType.SNAPSHOT, if_os="linux"))
    
    assert tool_result.status() == "Wrong OS"

def test_status_not_available():
    tool_result = ToolCheckResult(tool="test", desired_version="1.0", is_needed_for_os=True, is_available=False, is_snapshot=False, 
                                  found_version=None, parsed_version=None, is_compatible="Compatible", is_broken=False, 
                                  last_modified=None, tool_config=CliToolConfig(name="test", schema=SchemaType.SNAPSHOT, if_os="linux"))
    
    assert tool_result.status() == "Not available"

def test_status_existence_schema():
    tool_result = ToolCheckResult(tool="test", desired_version=None, is_needed_for_os=True, is_available=True, is_snapshot=False, 
                                  found_version=None, parsed_version=None, is_compatible="Compatible", is_broken=False, 
                                  last_modified=None, tool_config=CliToolConfig(name="test", schema=SchemaType.EXISTENCE, if_os="linux"))
    
    assert tool_result.status() == "Compatible"

def test_status_broken_tool():
    tool_result = ToolCheckResult(tool="test", desired_version="1.0", is_needed_for_os=True, is_available=True, is_snapshot=False, 
                                  found_version="1.0", parsed_version="1.0", is_compatible="Compatible", is_broken=True, 
                                  last_modified=None, tool_config=CliToolConfig(name="test", version="1.0", schema=SchemaType.SNAPSHOT, if_os="linux"))
    
    assert tool_result.status() == "Can't run"

def test_is_problem_true():
    tool_result = ToolCheckResult(tool="test", desired_version="1.0", is_needed_for_os=True, is_available=False, is_snapshot=False, 
                                  found_version=None, parsed_version=None, is_compatible="Compatible", is_broken=False, 
                                  last_modified=None, tool_config=CliToolConfig(name="test", schema=SchemaType.SNAPSHOT, if_os="linux"))
    
    assert tool_result.is_problem()

def test_is_problem_false():
    tool_result = ToolCheckResult(tool="test", desired_version="1.0", is_needed_for_os=True, is_available=True, is_snapshot=False, 
                                  found_version="1.0", parsed_version="1.0", is_compatible="Compatible", is_broken=False, 
                                  last_modified=None, tool_config=CliToolConfig(name="test", version="1.0", schema=SchemaType.SNAPSHOT, if_os="linux"))
    
    assert not tool_result.is_problem()

def test_tool_availability_result():
    availability_result = ToolAvailabilityResult(is_available=True, is_broken=False, version="1.0", last_modified=None)
    
    assert availability_result.is_available
    assert not availability_result.is_broken
    assert availability_result.version == "1.0"
    assert availability_result.last_modified is None

# No more unit tests
# ### Next Unit Test
# 

def test_status_compatible():
    mock_tool_config = Mock(name="mock_tool_config", schema=SchemaType.SNAPSHOT)
    tool_result = ToolCheckResult(tool="test", desired_version="1.0", is_needed_for_os=True, is_available=True, is_snapshot=False, 
                                  found_version="1.0", parsed_version="1.0", is_compatible="Compatible", is_broken=False, 
                                  last_modified=None, tool_config=mock_tool_config)
    
    assert tool_result.status() == "Compatible"

# No more unit tests
# ### Next Unit Test
# 

def test_tool_availability_result():
    mock_last_modified = datetime(year=2023, month=1, day=15, hour=12, minute=30)
    availability_result = ToolAvailabilityResult(is_available=True, is_broken=True, version="2.0", last_modified=mock_last_modified)
    
    assert availability_result.is_available
    assert availability_result.is_broken
    assert availability_result.version == "2.0"
    assert availability_result.last_modified == mock_last_modified

# No more unit tests
# ### Next Unit Test
# 

def test_cache_hash_empty_config():
    config = CliToolConfig(name="test")
    
    expected_hash = "021dec0093556595be08d19057a60f07"  # Hash of empty string
    
    assert config.cache_hash() == expected_hash

# No more unit tests
# ### Next Unit Test
# 

def test_is_problem_false_not_needed_for_os():
    tool_result = ToolCheckResult(tool="test", desired_version="1.0", is_needed_for_os=False, is_available=True, is_snapshot=False, 
                                  found_version="1.0", parsed_version="1.0", is_compatible="Compatible", is_broken=False, 
                                  last_modified=None, tool_config=Mock(name="mock_tool_config", schema=SchemaType.SNAPSHOT, if_os="linux"))
    
    assert not tool_result.is_problem()

# No more unit tests
