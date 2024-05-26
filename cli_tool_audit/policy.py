"""
Apply various policies to the results of the tool checks.
"""

import cli_tool_audit.models as models


def apply_policy(results: list[models.ToolCheckResult]) -> bool:
    """
    Pretty print the results of the validation.

    Args:
        results (list[models.ToolCheckResult]): A list of ToolCheckResult objects.

    Returns:
        bool: True if any of the tools failed validation, False otherwise.
    """
    failed = False
    for result in results:
        if result.is_broken:
            failed = True
        elif not result.is_available:
            failed = True

        if not result.is_compatible:
            failed = True

    return failed
