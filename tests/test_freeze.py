from cli_tool_audit.freeze import freeze_to_screen
from cli_tool_audit.models import SchemaType


def test_freeze_to_screen():
    # just run
    freeze_to_screen(["pip", "python"], schema=SchemaType.SEMVER)
