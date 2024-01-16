import os
from dataclasses import dataclass
from typing import Any, Optional, cast

import toml
import tomlkit


@dataclass
class CliToolConfig:
    version: Optional[str] = None
    version_snapshot: Optional[str] = None
    version_switch: Optional[str] = None
    only_check_existence: Optional[bool] = False
    schema: Optional[str] = None
    if_os: Optional[str] = None
    version_stamp: Optional[str] = None
    source: Optional[str] = None


class ConfigManager:
    """
    Manage the config file.
    """

    def __init__(self, config_path: str) -> None:
        """
        Args:
            config_path (str): The path to the toml file.
        """
        self.config_path = config_path
        self.tools: dict[str, CliToolConfig] = {}

    def read_config(self) -> bool:
        """
        Read the cli-tools section from a toml file.
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, encoding="utf-8") as file:
                config = toml.load(file)
                tools_config = config.get("tool", {}).get("cli-tools", {})
                for tool_name, settings in tools_config.items():
                    self.tools[tool_name] = CliToolConfig(**settings)
        return bool(self.tools)

    def create_tool_config(self, tool_name: str, config: dict) -> None:
        """
        Create a new tool config.
        Args:
            tool_name (str): The name of the tool.
            config (dict): The config for the tool.
        """
        if not self.tools:
            self.read_config()
        if tool_name in self.tools:
            raise ValueError(f"Tool {tool_name} already exists")
        self.tools[tool_name] = CliToolConfig(**config)
        self._save_config()

    def update_tool_config(self, tool_name: str, config: dict) -> None:
        """
        Update an existing tool config.
        Args:
            tool_name (str): The name of the tool.
            config (dict): The config for the tool.
        """
        if not self.tools:
            self.read_config()
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} does not exist")
        for key, value in config.items():
            setattr(self.tools[tool_name], key, value)
        self._save_config()

    def create_update_tool_config(self, tool_name: str, config: dict) -> None:
        """
        Create or update a tool config.
        Args:
            tool_name (str): The name of the tool.
            config (dict): The config for the tool.
        """
        if not self.tools:
            self.read_config()
        if tool_name not in self.tools:
            self.tools[tool_name] = CliToolConfig(**config)
        else:
            for key, value in config.items():
                setattr(self.tools[tool_name], key, value)
        self._save_config()

    def delete_tool_config(self, tool_name: str) -> None:
        """
        Delete an existing tool config.
        Args:
            tool_name (str): The name of the tool.
        """
        if not self.tools:
            self.read_config()
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} does not exist")
        del self.tools[tool_name]
        self._save_config()

    def _save_config(self) -> None:
        """
        Save the config to the file.
        """
        # Read the entire existing config
        if os.path.exists(self.config_path):
            with open(self.config_path, encoding="utf-8") as file:
                config = tomlkit.parse(file.read())
        else:
            config = tomlkit.document()

        # Access or create the 'cli-tools' section
        # tools_section = config.get('tool', {}).get('cli-tools', {})
        if "tool" not in config:
            config["tool"] = tomlkit.table()
        if "cli-tools" not in cast(Any, config.get("tool")):
            cast(Any, config["tool"])["cli-tools"] = tomlkit.table()

        # Update the 'cli-tools' section with inline tables
        for tool_name, tool_config in self.tools.items():
            inline_table = tomlkit.inline_table()
            for key, value in vars(tool_config).items():
                if value is not None:
                    if key == "only_check_existence" and value is False:
                        pass
                    else:
                        inline_table[key] = value
            cast(Any, cast(Any, config["tool"])["cli-tools"])[tool_name] = inline_table

        # Write the entire config back to the file
        with open(self.config_path, "w", encoding="utf-8") as file:
            file.write(tomlkit.dumps(config))


if __name__ == "__main__":
    # Usage example
    config_manager = ConfigManager("../pyproject.toml")
    c = config_manager.read_config()
    print(c)
