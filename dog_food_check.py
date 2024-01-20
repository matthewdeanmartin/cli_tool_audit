import sys

import cli_tool_audit
import cli_tool_audit.models as models


def run()->None:
    config = models.CliToolConfig(
        schema=models.SchemaType.SEMVER,
        version_switch="--version",
        tags=[],
        name="cli_tool_audit",
        version=cli_tool_audit.__version__
    )
    result = cli_tool_audit.process_tools({"cli_tool_audit": config},
                                 no_cache=True,
                                 disable_progress_bar=True)
    if result[0].is_available:
        raise TypeError(f"Should something is wrong {result[0]}")

if __name__ == '__main__':
    sys.exit(run())

