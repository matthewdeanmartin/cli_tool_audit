import pkgutil
import subprocess
from pathlib import Path
from typing import Any
import cli_tool_audit

def get_submodules(module: Any) -> list[str]:
    """
    Discovers all submodules in the given module.

    Args:
        module: The module to discover submodules in.

    Returns:
        A list of submodule names.
    """
    package_path = module.__path__
    return [name for _, name, _ in pkgutil.iter_modules(package_path)]


def generate_hypothesis_tests(module: Any) -> None:
    """
    Generates and executes Hypothesis test commands for each submodule in the given module.

    Args:
        module: The module to generate tests for.
    """
    submodules = get_submodules(module)
    base_command = ['hypothesis', 'write', '--style', 'pytest', '--annotate']
    output_dir = Path('tests/test_hypothesis/')
    output_dir.mkdir(parents=True, exist_ok=True)

    for submodule in submodules:
        module_name = f'{module.__name__}.{submodule}'
        test_file_name = f'test_{submodule}.py'
        output_path = output_dir / test_file_name
        command = base_command + [module_name]

        with open(output_path, 'w') as file:
            print(command)
            subprocess.run(command, stdout=file, text=True, check=True)


# Example usage:

if __name__ == '__main__':
    generate_hypothesis_tests(cli_tool_audit)
