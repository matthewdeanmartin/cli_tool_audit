"""
Audit CLI tool version numbers.

.. include:: ../README.md
"""
__all__ = ["validate", "read_config", "check_tool_availability", "__version__", "__about__"]

import cli_tool_audit.__about__ as __about__
from cli_tool_audit.__about__ import __version__
from cli_tool_audit.call_tools import check_tool_availability
from cli_tool_audit.config_reader import read_config
from cli_tool_audit.views import validate
