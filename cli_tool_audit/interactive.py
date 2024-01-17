"""
Interactively manage tool configurations.
"""
from cli_tool_audit.config_manager import ConfigManager


def interactive_config_manager(config_manager: ConfigManager) -> None:
    """
    Interactively manage tool configurations.

    Args:
        config_manager (ConfigManager): The configuration manager instance.
    """
    while True:
        print("\nCLI Tool Configuration Manager")
        print("1. Create or update tool configuration")
        print("2. Delete tool configuration")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            tool_name = input("\nEnter the name of the tool or enter to accept default: ")
            config = {}

            # Check existence only
            only_check_existence = input("Check existence only? (yes/no) Default no: ").lower()
            if only_check_existence.startswith("y"):
                config["only_check_existence"] = only_check_existence

            if not only_check_existence.startswith("y"):
                # Schema
                schema = input("Enter schema, semver or snapshot (default is semver): ")
                if schema:
                    config["schema"] = schema

                # Version
                if schema != "snapshot":
                    version = input("Enter the desired version (default is *, any version): ")
                    if version:
                        config["version"] = version

            # Version switch
            version_switch = input("Enter the version switch (default is --version): ")
            if version_switch:
                config["version_switch"] = version_switch

            #
            # OS-specific
            if_os = input(
                "Enter OS restriction, aix, emscripten, linux, wasi, win32, cygwin, darwin, etc. (default is all platforms): "
            )
            if if_os:
                config["if_os"] = if_os

            config_manager.create_update_tool_config(tool_name, config)
            print(f"Configuration for '{tool_name}' updated.")

        elif choice == "2":
            tool_name = input("\nEnter the name of the tool to delete: ")
            config_manager.delete_tool_config(tool_name)
            print(f"Configuration for '{tool_name}' deleted.")

        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")


# Example usage
# config_manager = ConfigManager("path_to_your_config.toml")
# interactive_config_manager(config_manager)
