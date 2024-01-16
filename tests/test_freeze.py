from cli_tool_audit.freeze import freeze_to_screen


def test_freeze_to_screen():
    # just run
    freeze_to_screen(["pip", "python"])
