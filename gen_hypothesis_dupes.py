import re
from collections import Counter
from pathlib import Path


def count_test_functions(test_dir: str) -> None:
    """
    Counts the occurrences of each test function in .py files within the specified directory.

    Args:
        test_dir: The directory containing the test files.
    """
    test_files = Path(test_dir).glob('test_*.py')
    test_function_pattern = re.compile(r'def (test_[a-zA-Z0-9_]*\()')

    function_counts = Counter()

    for test_file in test_files:
        with open(test_file) as file:
            content = file.read()
            function_names = test_function_pattern.findall(content)
            function_names = [name[:-1] for name in function_names]  # Remove trailing '(' from function names
            function_counts.update(function_names)

    # Filter and print functions that are tested more than once
    for function_name, count in function_counts.items():
        if count > 1:
            print(f"{function_name}: {count} times")


if __name__ == '__main__':
    # Example usage:
    count_test_functions('tests/test_hypothesis')
