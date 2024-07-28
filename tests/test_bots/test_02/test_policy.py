from cli_tool_audit.models import ToolCheckResult
from unittest.mock import Mock
import cli_tool_audit.policy as policy





# ### Bug
# 
# I don't see any bugs in the `apply_policy` function. It looks like it correctly
# iterates over the results list and sets `failed` to True if any result indicates
# a failure.
# 
# ### Proposed Unit Test
# 
# I will write a pytest unit test that covers the following scenarios:
# 
# 1. Test when all results pass.
# 2. Test when at least one tool is broken.
# 3. Test when at least one tool is not available.
# 4. Test when at least one tool is incompatible.
# 5. Test when multiple tools have different statuses.
# 
# Let's write the unit test now:

def test_apply_policy():
    # Prepare test data
    result1 = Mock(spec=ToolCheckResult, is_broken=False, is_available=True, is_compatible=True)
    result2 = Mock(spec=ToolCheckResult, is_broken=False, is_available=True, is_compatible=True)
    results_pass = [result1, result2]

    result3 = Mock(spec=ToolCheckResult, is_broken=True, is_available=True, is_compatible=True)
    result4 = Mock(spec=ToolCheckResult, is_broken=False, is_available=False, is_compatible=True)
    result5 = Mock(spec=ToolCheckResult, is_broken=False, is_available=True,  is_compatible=False)
    results_fail = [result3, result4, result5]

    # Test all results pass
    assert policy.apply_policy(results_pass) == False

    # Test at least one tool is broken
    assert policy.apply_policy([result1, result2, result3]) == True

    # Test at least one tool is not available
    assert policy.apply_policy([result1, result4, result2]) == True

    # Test at least one tool is incompatible
    assert policy.apply_policy([result1, result5, result2]) == True

    # Test multiple tools have different statuses
    assert policy.apply_policy(results_pass + results_fail) == True

# 
# 
# ### No more unit tests.
