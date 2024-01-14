from cli_tool_audit.compatibility import check_compatibility


def test_not_compatible():
    assert check_compatibility(">1.0.0", "0.1.0") != "Compatible"


def test_compatible():
    assert check_compatibility(">1.0", "2.0") == "Compatible"
    assert check_compatibility(">1.0.0", "2.0") == "Compatible"
    assert check_compatibility(">=2.10", "2.10") == "Compatible"

    assert check_compatibility(">=2.10", "2.10") == "Compatible"
    assert check_compatibility(">=2.10", "vulture 2.10") == "Compatible"
