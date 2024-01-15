import toml
from dataclasses import dataclass, field
from typing import Optional, Dict

import tomlkit


@dataclass
class CliToolConfig:
    version: Optional[str] = None
    version_switch: Optional[str] = None
    only_check_existence: bool = False
    schema: Optional[str] = None
    if_os: Optional[str] = None
    version_stamp: Optional[str] = None
    source: Optional[str] = None

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.tools = {}

    def read_config(self):
        with open(self.config_path, 'r') as file:
            config = toml.load(file)
            tools_config = config.get("tool", {}).get("cli-tools", {})
            for tool_name, settings in tools_config.items():
                self.tools[tool_name] = CliToolConfig(**settings)

    def create_tool_config(self, tool_name: str, config: Dict):
        if tool_name in self.tools:
            raise ValueError(f"Tool {tool_name} already exists")
        self.tools[tool_name] = CliToolConfig(**config)
        self._save_config()

    def update_tool_config(self, tool_name: str, config: Dict):
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} does not exist")
        for key, value in config.items():
            setattr(self.tools[tool_name], key, value)
        self._save_config()

    def delete_tool_config(self, tool_name: str):
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} does not exist")
        del self.tools[tool_name]
        self._save_config()

    def _save_config(self):
        # Read the entire existing config
        with open(self.config_path, 'r') as file:
            config = tomlkit.parse(file.read())

        # Access or create the 'cli-tools' section
        tools_section = config.get('tool', {}).get('cli-tools', {})
        if 'tool' not in config:
            config['tool'] = tomlkit.table()
        if 'cli-tools' not in config['tool']:
            config['tool']['cli-tools'] = tomlkit.table()

        # Update the 'cli-tools' section with inline tables
        for tool_name, tool_config in self.tools.items():
            inline_table = tomlkit.inline_table()
            for key, value in vars(tool_config).items():
                if value is not None:
                    inline_table[key] = value
            config['tool']['cli-tools'][tool_name] = inline_table

        # Write the entire config back to the file
        with open(self.config_path, 'w') as file:
            file.write(tomlkit.dumps(config))

if __name__ == '__main__':
    # Usage example
    config_manager = ConfigManager('../pyproject.toml')
    c = config_manager.read_config()
    print(c)
