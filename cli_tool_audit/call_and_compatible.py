"""
Merge tool call and compatibility check results.
"""

import sys
import threading

import cli_tool_audit.audit_cache as audit_cache
import cli_tool_audit.audit_manager as audit_manager
import cli_tool_audit.models as models

# Old interface


def check_tool_wrapper(
    tool_info: tuple[str, models.CliToolConfig, threading.Lock, bool],
) -> models.ToolCheckResult:
    """
    Wrapper function for check_tool_availability() that returns a ToolCheckResult object.

    Args:
        tool_info (tuple[str, models.CliToolConfig, threading.Lock, bool]): A tuple containing the tool name, the
        CliToolConfig object, a lock, and a boolean indicating if the cache is enabled.

    Returns:
        models.ToolCheckResult: A ToolCheckResult object.
    """
    tool, config, lock, enable_cache = tool_info

    if config.if_os and not sys.platform.startswith(config.if_os):
        # This isn't very transparent about what just happened
        return models.ToolCheckResult(
            is_needed_for_os=False,
            tool=tool,
            desired_version=config.version or "0.0.0",
            is_available=False,
            found_version=None,
            parsed_version=None,
            is_snapshot=False,
            is_compatible=f"{sys.platform}, not {config.if_os}",
            is_broken=False,
            last_modified=None,
            tool_config=config,
        )

    config.name = tool
    config.version_switch = config.version_switch or "--version"

    if enable_cache:
        cached_manager = audit_cache.AuditFacade()
        with lock:
            return cached_manager.call_and_check(tool_config=config)

    manager = audit_manager.AuditManager()
    return manager.call_and_check(tool_config=config)
