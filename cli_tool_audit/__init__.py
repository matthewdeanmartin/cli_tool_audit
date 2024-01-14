"""
Audit CLI tool version numbers.
"""
__all__ = ["validate", "read_config", "check_tool_availability", "__version__"]

from cli_tool_audit._version import __version__
from cli_tool_audit.call_tools import check_tool_availability, read_config
from cli_tool_audit.views import validate
