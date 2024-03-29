from pathlib import Path

import cli_tool_audit


def test_with_live_tools() -> None:
    """Example"""
    # Example usage
    file_path = "../pyproject.toml"
    cli_tools = cli_tool_audit.read_config(Path(file_path))

    count = 0
    for tool, config in cli_tools.items():
        count += 1
        result = cli_tool_audit.check_tool_availability(
            tool, schema=config.schema, version_switch=config.version_switch
        )
        print(
            f"{tool}: {'Available' if result.is_available else 'Not Available'}"
            f" - Version: { result.version if  result.version else 'N/A'}"
        )
        if count >= 5:
            break
