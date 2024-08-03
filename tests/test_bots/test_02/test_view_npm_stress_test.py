import pytest

# 1. We will write a unit test to ensure that the `list_global_npm_executables`
#    function correctly lists the executables in the global node_modules path.
# 2. We will write a unit test to ensure that the `report_for_npm_tools` function
#    generates the expected ToolCheckResult objects.
# 3. We will write a unit test to ensure that the `report_for_npm_tools` function
#    handles the case when the maximum count is set.
# 4. We will write a unit test to ensure that the `report_for_npm_tools` function
#    correctly processes the ToolCheckResult objects and prints the results
#    properly.
#
# Here are the unit tests:


@pytest.fixture
def mock_listdir(tmp_path):
    test_path = tmp_path / "test_node_modules"
    test_path.mkdir()
    (test_path / "executable1").touch()
    (test_path / "executable2").touch()
    return test_path
