"""
Static version file for cli_tool_audit
"""
# Version check to make mypy happy.... but our minimum version is 3.8 right now.
# if sys.version_info[:2] >= (3, 8):
import importlib.metadata as importlib_metadata

# else:
#     import importlib_metadata

try:
    __version__ = importlib_metadata.version("cli-tool-audit")
except importlib_metadata.PackageNotFoundError:
    __version__ = "1.1.0"
