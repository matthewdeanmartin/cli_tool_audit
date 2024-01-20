import copy
import os
from pathlib import Path
from typing import Any, cast

import toml
import tomlkit

import cli_tool_audit.models as models


class ConfigManager:
    """
    Manage the config file.
    """

    def __init__(self, config_path: Path) -> None:
        """
        Args:
            config_path (Path): The path to the toml file.
        """
        self.config_path = config_path
        self.tools: dict[str, models.CliToolConfig] = {}

    def read_config(self) -> bool:
        """
        Read the cli-tools section from a toml file.

        Returns:
            bool: True if the cli-tools section exists, False otherwise.
        """
        if self.config_path.exists():
            with open(str(self.config_path), encoding="utf-8") as file:
                # okay this is too hard.
                # from tomlkit.items import Item
                # class SchemaTypeItem(Item):
                #     def __init__(self, value:SchemaType):
                #         self.value = value
                #     def as_string(self):
                #         return str(self.value)
                #
                # def encoder(value):
                #     if isinstance(value, SchemaType):
                #         return SchemaTypeItem(value.value)
                #     raise TypeError(f"Unknown type {type(value)}")
                # tomlkit.register_encoder(lambda x: x.value)
                # TODO: switch to tomkit and clone the config/settings
                # so that we can use it like ordinary python
                config = toml.load(file)
                tools_config = config.get("tool", {}).get("cli-tools", {})
                for tool_name, settings in tools_config.items():
                    if settings.get("only_check_existence"):
                        settings["schema"] = models.SchemaType.EXISTENCE
                        del settings["only_check_existence"]
                    elif settings.get("version_snapshot"):
                        settings["schema"] = models.SchemaType.SNAPSHOT
                        settings["version"] = settings.get("version_snapshot")
                        del settings["version_snapshot"]

                    settings["name"] = tool_name
                    if settings.get("schema"):
                        settings["schema"] = models.SchemaType(settings["schema"].lower())
                    else:
                        settings["schema"] = models.SchemaType.SEMVER
                    self.tools[tool_name] = models.CliToolConfig(**settings)
        return bool(self.tools)

    def create_tool_config(self, tool_name: str, config: dict) -> None:
        """
        Create a new tool config.

        Args:
            tool_name (str): The name of the tool.
            config (dict): The config for the tool.

        Raises:
            ValueError: If the tool already exists.
        """
        if not self.tools:
            self.read_config()
        if tool_name in self.tools:
            raise ValueError(f"Tool {tool_name} already exists")
        config["name"] = tool_name
        self.tools[tool_name] = models.CliToolConfig(**config)
        self._save_config()

    def update_tool_config(self, tool_name: str, config: dict) -> None:
        """
        Update an existing tool config.
        Args:
            tool_name (str): The name of the tool.
            config (dict): The config for the tool.

        Raises:
            ValueError: If the tool does not exist.
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
            config["name"] = tool_name
            self.tools[tool_name] = models.CliToolConfig(**config)
        else:
            for key, value in config.items():
                if key == "schema":
                    value = str(models.SchemaType(value))
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
            return
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
        if "tool" not in config:
            config["tool"] = tomlkit.table()
        if "cli-tools" not in cast(Any, config.get("tool")):
            cast(Any, config["tool"])["cli-tools"] = tomlkit.table()

        # Update the 'cli-tools' section with inline tables
        for tool_name, tool_config in self.tools.items():
            inline_table = tomlkit.inline_table()
            for key, value in vars(tool_config).items():
                if value is not None:
                    # TODO: could use custom toml encoder here?
                    if key == "schema":
                        value = str(value)
                    inline_table[key] = value
            cast(Any, cast(Any, config["tool"])["cli-tools"])[tool_name] = inline_table

        # Handle deletes
        for tool in copy.deepcopy(cast(Any, cast(Any, config["tool"])["cli-tools"])):
            if tool not in self.tools:
                del cast(Any, cast(Any, config["tool"])["cli-tools"])[tool]

        # Write the entire config back to the file
        with open(self.config_path, "w", encoding="utf-8") as file:
            file.write(tomlkit.dumps(config))


if __name__ == "__main__":
    # Usage example
    def run() -> None:
        """Example"""
        config_manager = ConfigManager(Path("../pyproject.toml"))
        c = config_manager.read_config()
        print(c)

    run()
