"""Metadata for cli_tool_audit."""

__all__ = [
    "__credits__",
    "__dependencies__",
    "__description__",
    "__keywords__",
    "__readme__",
    "__requires_python__",
    "__status__",
    "__title__",
    "__version__",
]

__title__ = "cli_tool_audit"
__version__ = "3.2.0"
__description__ = "Audit for existence and version number of cli tools."
__credits__ = [{"name": "Matthew Martin", "email": "matthewdeanmartin@gmail.com"}]
__readme__ = "README.md"
__requires_python__ = ">=3.11"
__keywords__ = ["cli tooling", "version numbers"]
__status__ = "4 - Beta"
__dependencies__ = [
    "whichcraft>=0.6.1",
    "semver>=3.0.2",
    "packaging>=23.2",
    "prettytable>=3.9.0",
    "colorama>=0.4.6",
    "colorlog>=6.8.0",
    "tqdm>=4.66.1",
    "toml>=0.10.2",
    "tomlkit>=0.12.3",
]
