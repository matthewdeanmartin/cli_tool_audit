"""
This module provides a facade for the audit manager that caches results.
"""

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Optional

import cli_tool_audit.audit_manager as audit_manager
from cli_tool_audit.json_utils import custom_json_serializer
from cli_tool_audit.models import CliToolConfig, ToolCheckResult


def custom_json_deserializer(data: dict[str, Any]) -> dict[str, Any]:
    """
    Custom JSON deserializer for objects not deserializable by default json code.
    Args:
        data (dict[str,Any]): The object to deserialize.

    Returns:
        dict[str,Any]: A JSON deserializable representation of the object.
    """
    if "last_modified" in data and data["last_modified"]:
        data["last_modified"] = datetime.datetime.fromisoformat(data["last_modified"])
    return data


logger = logging.getLogger(__name__)


class AuditFacade:
    def __init__(self, cache_dir: Optional[str] = None) -> None:
        """
        Initialize the facade.
        Args:
            cache_dir (Optional[str], optional): The directory to use for caching. Defaults to None.
        """
        self.audit_manager = audit_manager.AuditManager()
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / ".cli_tool_audit_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_filename(self, tool_config: CliToolConfig) -> Path:
        """
        Get the cache filename for the given tool.
        Args:
            tool_config (CliToolConfig): The tool to get the cache filename for.

        Returns:
            Path: The cache filename.
        """
        sanitized_name = tool_config.name.replace(".", "_")
        the_hash = tool_config.cache_hash()
        return self.cache_dir / f"{sanitized_name}_{the_hash}.json"

    def read_from_cache(self, tool_config: CliToolConfig) -> Optional[ToolCheckResult]:
        """
        Read the cached result for the given tool.
        Args:
            tool_config (CliToolConfig): The tool to get the cached result for.

        Returns:
            Optional[ToolCheckResult]: The cached result or None if not found.
        """
        cache_file = self.get_cache_filename(tool_config)
        if cache_file.exists():
            with open(cache_file, encoding="utf-8") as file:
                logger.debug(f"Cache hit for {tool_config.name}")
                return ToolCheckResult(**json.load(file, object_hook=custom_json_deserializer))
        logger.debug(f"Cache miss for {tool_config.name}")
        return None

    def write_to_cache(self, tool_config: CliToolConfig, result: ToolCheckResult) -> None:
        """
        Write the given result to the cache.
        Args:
            tool_config (CliToolConfig): The tool to write the result for.
            result (ToolCheckResult): The result to write.
        """
        cache_file = self.get_cache_filename(tool_config)
        with open(cache_file, "w", encoding="utf-8") as file:
            logger.debug(f"Caching {tool_config.name}")
            json.dump(result.__dict__, file, ensure_ascii=False, indent=4, default=custom_json_serializer)

    def call_and_check(self, tool_config: CliToolConfig) -> ToolCheckResult:
        """
        Call and check the given tool.
        Args:
            tool_config (CliToolConfig): The tool to call and check.

        Returns:
            ToolCheckResult: The result of the check.
        """
        cached_result = self.read_from_cache(tool_config)
        if cached_result:
            return cached_result

        result = self.audit_manager.call_and_check(tool_config)
        if not result.is_problem():
            # Don't cache problems. Assume user will fix it soon.
            self.write_to_cache(tool_config, result)
        return result
