"""
Merge tool call and compatibility check results.
"""
import sys
from typing import cast

import cli_tool_audit.call_tools as cli_availability
from cli_tool_audit.compatibility import check_compatibility
from cli_tool_audit.models import CliToolConfig, ToolCheckResult


def check_tool_wrapper(tool_info: tuple[str, CliToolConfig]) -> ToolCheckResult:
    """
    Wrapper function for check_tool_availability() that returns a ToolCheckResult object.

    Args:
        tool_info (tuple[str, CliToolConfig]): A tuple containing the tool name and the tool configuration.

    Returns:
        ToolCheckResult: A ToolCheckResult object.
    """
    tool, config = tool_info

    if config.if_os and not sys.platform.startswith(config.if_os):
        # This isn't very transparent about what just happened
        return ToolCheckResult(
            tool=tool,
            desired_version=config.version or "0.0.0",
            is_available=False,
            found_version=None,
            parsed_version=None,
            is_snapshot=False,
            is_compatible=f"{sys.platform}, not {config.if_os}",
            is_broken=False,
            last_modified=None,
        )
    result = cli_availability.check_tool_availability(
        tool, config.version_switch or "--version", cast(bool, config.only_check_existence or False)
    )

    parsed_version = None
    if config.version_snapshot:
        desired_version = config.version_snapshot if result.version != config.version_snapshot else "Same"
        if config.version_snapshot and result.version == config.version_snapshot:
            is_compatible = "Compatible"
        else:
            is_compatible = "Snapshot differs"
    else:
        desired_version = config.version or "0.0.0"
        parsed_version = None
        if config.only_check_existence and result.is_available:
            is_compatible = "Compatible"
        else:
            is_compatible, parsed_version = check_compatibility(desired_version, found_version=result.version)

    return ToolCheckResult(
        tool=tool,
        desired_version=desired_version,
        is_available=result.is_available,
        is_snapshot=bool(config.version_snapshot),
        found_version=result.version,
        parsed_version=parsed_version,
        is_compatible=is_compatible,
        is_broken=result.is_broken,
        last_modified=result.last_modified,
    )
