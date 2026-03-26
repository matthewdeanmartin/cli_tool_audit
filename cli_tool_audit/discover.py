"""
Discover CLI tool references in common project files.

Scans Makefile, GitHub Actions workflows, package.json, pyproject.toml,
Dockerfile, shell scripts, and .pre-commit-config.yaml to find tool names.
"""

import re
import shlex
from pathlib import Path

# Tools that are too generic or OS-level to be useful to audit
_IGNORE = {
    "echo",
    "cat",
    "ls",
    "cd",
    "rm",
    "mkdir",
    "cp",
    "mv",
    "grep",
    "awk",
    "sed",
    "find",
    "chmod",
    "chown",
    "export",
    "set",
    "source",
    "true",
    "false",
    "env",
    "test",
    "if",
    "then",
    "else",
    "fi",
    "do",
    "done",
    "for",
    "while",
    "sh",
    "bash",
    "zsh",
    "python",  # usually present; users can add explicitly
    "python3",
    "pip",
    "pip3",
    "sudo",
    "su",
    "curl",
    "wget",
    "tar",
    "gzip",
    "unzip",
    "xargs",
    "sort",
    "uniq",
    "head",
    "tail",
    "wc",
    "date",
    "printf",
    "read",
    "exit",
    "return",
    "eval",
    "exec",
    "trap",
    "wait",
    "kill",
    "sleep",
    "touch",
    "tee",
    "cut",
    "tr",
    "diff",
    "patch",
    "type",
    "which",
    "command",
    "hash",
    "pwd",
    "dirname",
    "basename",
    "ln",
    "stat",
    "file",
    "strings",
    "xxd",
    "od",
    "dd",
    "mount",
    "umount",
    "df",
    "du",
    "ps",
    "top",
    "pkill",
    "pgrep",
    "nohup",
    "nice",
    "renice",
}

# Regex for a word that looks like a CLI tool name (no path separators, not a flag)
_TOOL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_\-]{1,40}$")


def _is_tool_candidate(word: str) -> bool:
    return bool(_TOOL_RE.match(word)) and word not in _IGNORE


def _first_word_of_shell_line(line: str) -> str | None:
    """Return the first word of a shell command line, or None."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    try:
        tokens = shlex.split(line)
    except ValueError:
        tokens = line.split()
    if tokens and _is_tool_candidate(tokens[0]):
        return tokens[0]
    return None


def _scan_makefile(path: Path) -> set[str]:
    """Extract tools from recipe lines in a Makefile."""
    tools: set[str] = set()
    if not path.exists():
        return tools
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        # Recipe lines start with a tab
        if line.startswith("\t"):
            cmd = line.lstrip("\t").strip()
            # Handle $(VENV) prefix pattern common in this project
            cmd = re.sub(r"^\$\([A-Z_]+\)\s*", "", cmd)
            tool = _first_word_of_shell_line(cmd)
            if tool:
                tools.add(tool)
    return tools


def _scan_github_workflows(root: Path) -> set[str]:
    """Extract tools from 'run:' lines in GitHub Actions workflow YAML files."""
    tools: set[str] = set()
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.exists():
        return tools
    for yml_path in workflows_dir.glob("*.yml"):
        text = yml_path.read_text(encoding="utf-8", errors="ignore")
        in_run_block = False
        for line in text.splitlines():
            stripped = line.strip()
            # Match `run: <cmd>` or `- run: <cmd>` (single-line)
            m = re.match(r"(?:-\s+)?run:\s+(.+)", stripped)
            if m:
                in_run_block = False
                value = m.group(1).strip()
                if value == "|" or value == ">":
                    in_run_block = True
                else:
                    for part in re.split(r"&&|\|\|", value):
                        tool = _first_word_of_shell_line(part.strip())
                        if tool:
                            tools.add(tool)
            elif in_run_block:
                # Inside a YAML block scalar — collect shell lines
                if not stripped or re.match(r"\w+:|^-\s", stripped):
                    in_run_block = False
                else:
                    for part in re.split(r"&&|\|\|", stripped):
                        tool = _first_word_of_shell_line(part.strip())
                        if tool:
                            tools.add(tool)
    return tools


def _scan_package_json(path: Path) -> set[str]:
    """Extract tools from package.json scripts section."""
    tools: set[str] = set()
    if not path.exists():
        return tools

    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    for script_value in scripts.values():
        for part in re.split(r"&&|\||\||;", script_value):
            tool = _first_word_of_shell_line(part.strip())
            if tool:
                tools.add(tool)

    return tools


def _scan_pyproject_toml(path: Path) -> set[str]:
    """Extract tools from pyproject.toml [tool.hatch.envs.*.scripts] and [project.scripts]."""
    tools: set[str] = set()
    if not path.exists():
        return tools

    import toml

    data = toml.loads(path.read_text(encoding="utf-8"))
    # [tool.hatch.envs.*.scripts] values
    hatch_envs = data.get("tool", {}).get("hatch", {}).get("envs", {})
    for env_cfg in hatch_envs.values():
        for script_value in env_cfg.get("scripts", {}).values():
            if isinstance(script_value, str):
                tool = _first_word_of_shell_line(script_value)
                if tool:
                    tools.add(tool)
            elif isinstance(script_value, list):
                for line in script_value:
                    tool = _first_word_of_shell_line(line)
                    if tool:
                        tools.add(tool)

    return tools


def _scan_dockerfile(path: Path) -> set[str]:
    """Extract tools from RUN lines in a Dockerfile."""
    tools: set[str] = set()
    if not path.exists():
        return tools
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"RUN\s+(.+)", line.strip(), re.IGNORECASE)
        if m:
            run_cmd = m.group(1)
            for part in re.split(r"&&|\||\||;|\\", run_cmd):
                tool = _first_word_of_shell_line(part.strip())
                if tool:
                    tools.add(tool)
    return tools


def _scan_shell_scripts(root: Path) -> set[str]:
    """Extract tools from shell scripts in scripts/ directory."""
    tools: set[str] = set()
    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return tools
    for script in scripts_dir.iterdir():
        if script.suffix in (".sh", ".bash") or (
            script.is_file() and not script.suffix and script.stat().st_size < 100_000
        ):
            for line in script.read_text(encoding="utf-8", errors="ignore").splitlines():
                tool = _first_word_of_shell_line(line)
                if tool:
                    tools.add(tool)
    return tools


def _scan_pre_commit_config(path: Path) -> set[str]:
    """Extract repo/hook ids from .pre-commit-config.yaml."""
    tools: set[str] = set()
    if not path.exists():
        return tools

    import yaml  # type: ignore[import]

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for repo in data.get("repos", []):
        for hook in repo.get("hooks", []):
            hook_id = hook.get("id", "")
            if hook_id and _is_tool_candidate(hook_id):
                tools.add(hook_id)

    return tools


def discover_tools(root: Path | None = None) -> dict[str, list[str]]:
    """
    Scan a project directory for CLI tool references.

    Args:
        root: Root of the project directory. Defaults to current working directory.

    Returns:
        A dict mapping tool name -> list of source files where it was found.
    """
    if root is None:
        root = Path.cwd()

    sources: dict[str, list[str]] = {}

    def _add(tool: str, source: str) -> None:
        sources.setdefault(tool, [])
        if source not in sources[tool]:
            sources[tool].append(source)

    for tool in _scan_makefile(root / "Makefile"):
        _add(tool, "Makefile")
    for tool in _scan_makefile(root / "GNUmakefile"):
        _add(tool, "GNUmakefile")

    for tool in _scan_github_workflows(root):
        _add(tool, ".github/workflows")

    for tool in _scan_package_json(root / "package.json"):
        _add(tool, "package.json")

    for tool in _scan_pyproject_toml(root / "pyproject.toml"):
        _add(tool, "pyproject.toml")

    for tool in _scan_dockerfile(root / "Dockerfile"):
        _add(tool, "Dockerfile")

    for tool in _scan_shell_scripts(root):
        _add(tool, "scripts/")

    for tool in _scan_pre_commit_config(root / ".pre-commit-config.yaml"):
        _add(tool, ".pre-commit-config.yaml")

    return dict(sorted(sources.items()))
