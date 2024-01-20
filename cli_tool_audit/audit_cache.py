"""
This module provides a facade for the audit manager that caches results.
"""

import datetime
import json
import logging
import pathlib
from pathlib import Path
from typing import Any, Optional

import cli_tool_audit.audit_manager as audit_manager
import cli_tool_audit.json_utils as json_utils
import cli_tool_audit.models as models

__all__ = ["AuditFacade"]


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
    if "tool_config" in data and data["tool_config"]:
        for key, value in data["tool_config"].items():
            if isinstance(value, str) and key == "schema":
                data["tool_config"][key] = models.SchemaType(value)
        data["tool_config"] = models.CliToolConfig(**data["tool_config"])
    return data


logger = logging.getLogger(__name__)


class AuditFacade:
    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """
        Initialize the facade.
        Args:
            cache_dir (Optional[str], optional): The directory to use for caching. Defaults to None.
        """
        self.audit_manager = audit_manager.AuditManager()
        self.cache_dir = cache_dir if cache_dir else Path.cwd() / ".cli_tool_audit_cache"
        self.cache_dir.mkdir(exist_ok=True)
        with open(self.cache_dir / ".gitignore", "w", encoding="utf-8") as file:
            file.write("*\n!.gitignore\n")

        self.clear_old_cache_files()
        self.cache_hit = False

    def clear_old_cache_files(self) -> None:
        """
        Clear cache files that are older than 30 days.
        """
        current_time = datetime.datetime.now()
        expiration_days = 30
        for cache_file in self.cache_dir.glob("*.json"):
            file_creation_time = datetime.datetime.fromtimestamp(cache_file.stat().st_mtime)
            if (current_time - file_creation_time) > datetime.timedelta(days=expiration_days):
                if cache_file.exists():
                    cache_file.unlink(missing_ok=True)  # Delete the file

    def get_cache_filename(self, tool_config: models.CliToolConfig) -> Path:
        """
        Get the cache filename for the given tool.
        Args:
            tool_config (models.CliToolConfig): The tool to get the cache filename for.

        Returns:
            Path: The cache filename.
        """
        sanitized_name = tool_config.name.replace(".", "_")
        the_hash = tool_config.cache_hash()
        return self.cache_dir / f"{sanitized_name}_{the_hash}.json"

    def read_from_cache(self, tool_config: models.CliToolConfig) -> Optional[models.ToolCheckResult]:
        """
        Read the cached result for the given tool.
        Args:
            tool_config (models.CliToolConfig): The tool to get the cached result for.

        Returns:
            Optional[models.ToolCheckResult]: The cached result or None if not found.
        """
        cache_file = self.get_cache_filename(tool_config)
        if cache_file.exists():
            logger.debug(f"Cache hit for {tool_config.name}")
            try:
                with open(cache_file, encoding="utf-8") as file:
                    hit = models.ToolCheckResult(**json.load(file, object_hook=custom_json_deserializer))
                    self.cache_hit = True
                    return hit
            except TypeError:
                pathlib.Path(cache_file).unlink()
                self.cache_hit = False
                return None
        logger.debug(f"Cache miss for {tool_config.name}")
        self.cache_hit = False
        return None

    def write_to_cache(self, tool_config: models.CliToolConfig, result: models.ToolCheckResult) -> None:
        """
        Write the given result to the cache.
        Args:
            tool_config (models.CliToolConfig): The tool to write the result for.
            result (models.ToolCheckResult): The result to write.
        """
        cache_file = self.get_cache_filename(tool_config)
        with open(cache_file, "w", encoding="utf-8") as file:
            logger.debug(f"Caching {tool_config.name}")
            json.dump(result.__dict__, file, ensure_ascii=False, indent=4, default=json_utils.custom_json_serializer)

    def call_and_check(self, tool_config: models.CliToolConfig) -> models.ToolCheckResult:
        """
        Call and check the given tool.
        Args:
            tool_config (models.CliToolConfig): The tool to call and check.

        Returns:
            models.ToolCheckResult: The result of the check.
        """
        cached_result = self.read_from_cache(tool_config)
        if cached_result:
            return cached_result

        result = self.audit_manager.call_and_check(tool_config)
        if not result.is_problem():
            # Don't cache problems. Assume user will fix it soon.
            self.write_to_cache(tool_config, result)
        return result
