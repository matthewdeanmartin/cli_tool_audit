import cli_tool_audit


def test_with_live_tools() -> None:
    """Example"""
    # Example usage
    file_path = "../pyproject.toml"  # Replace with the path to your pyproject.toml
    cli_tools = cli_tool_audit.read_config(file_path)

    for tool, config in cli_tools.items():
        is_available, is_broken, version = cli_tool_audit.check_tool_availability(tool, config.get("version_switch"))
        print(f"{tool}: {'Available' if is_available else 'Not Available'} - Version: {version if version else 'N/A'}")
