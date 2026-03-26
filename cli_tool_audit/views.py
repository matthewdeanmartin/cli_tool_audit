"""
Main output view for cli_tool_audit assuming tool list is in config.
"""

import concurrent
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Union

import colorama
from prettytable import PrettyTable
from prettytable.colortable import ColorTable, Themes
from tqdm import tqdm

import cli_tool_audit.call_and_compatible as call_and_compatible
import cli_tool_audit.config_reader as config_reader
import cli_tool_audit.json_utils as json_utils
import cli_tool_audit.models as models
import cli_tool_audit.policy as policy

colorama.init(convert=True)

logger = logging.getLogger(__name__)


def validate(
    file_path: Path = Path("pyproject.toml"),
    no_cache: bool = False,
    tags: list[str] | None = None,
    disable_progress_bar: bool = False,
) -> list[models.ToolCheckResult]:
    """
    Validate the tools in the pyproject.toml file.

    Args:
        file_path (Path, optional): The path to the pyproject.toml file. Defaults to "pyproject.toml".
        no_cache (bool, optional): If True, don't use the cache. Defaults to False.
        tags (Optional[list[str]], optional): Only check tools with these tags. Defaults to None.
        disable_progress_bar (bool, optional): If True, disable the progress bar. Defaults to False.

    Returns:
        list[models.ToolCheckResult]: A list of ToolCheckResult objects.
    """
    if tags is None:
        tags = []
    cli_tools = config_reader.read_config(file_path)
    return process_tools(cli_tools, no_cache, tags, disable_progress_bar=disable_progress_bar)


def process_tools(
    cli_tools: dict[str, models.CliToolConfig],
    no_cache: bool = False,
    tags: list[str] | None = None,
    disable_progress_bar: bool = False,
) -> list[models.ToolCheckResult]:
    """
    Process the tools from a dictionary of CliToolConfig objects.

    Args:
        cli_tools (dict[str, models.CliToolConfig]): A dictionary of tool names and CliToolConfig objects.
        no_cache (bool, optional): If True, don't use the cache. Defaults to False.
        tags (Optional[list[str]], optional): Only check tools with these tags. Defaults to None.
        disable_progress_bar (bool, optional): If True, disable the progress bar. Defaults to False.

    Returns:
        list[models.ToolCheckResult]: A list of ToolCheckResult objects.
    """
    if tags:
        print(tags)
        cli_tools = {
            tool: config
            for tool, config in cli_tools.items()
            if config.tags and any(tag in config.tags for tag in tags)
        }

    # Determine the number of available CPUs
    num_cpus = os.cpu_count()

    enable_cache = len(cli_tools) >= 5
    # Create a ThreadPoolExecutor with one thread per CPU

    if no_cache:
        enable_cache = False
    lock = Lock()
    # Threaded appears faster.
    # lock = Dummy()
    # with ProcessPoolExecutor(max_workers=num_cpus) as executor:
    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        disable = should_show_progress_bar(cli_tools)
        with tqdm(total=len(cli_tools), disable=disable) as pbar:
            # Submit tasks to the executor
            futures = [
                executor.submit(call_and_compatible.check_tool_wrapper, (tool, config, lock, enable_cache))
                for tool, config in cli_tools.items()
            ]
            results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                pbar.update(1)
                results.append(result)
    return results


def get_default_tools() -> dict[str, models.CliToolConfig]:
    """Get a default set of tools to check if none are configured."""
    return {
        "python": models.CliToolConfig(name="python"),
        "java": models.CliToolConfig(name="java"),
        "node": models.CliToolConfig(name="node"),
        "go": models.CliToolConfig(name="go"),
        "rustc": models.CliToolConfig(name="rustc"),
        "make": models.CliToolConfig(name="make"),
        "git": models.CliToolConfig(name="git"),
    }


def report_from_pyproject_toml(
    file_path: Path | None = Path("pyproject.toml"),
    config_as_dict: dict[str, models.CliToolConfig] | None = None,
    exit_code_on_failure: bool = True,
    file_format: str = "table",
    no_cache: bool = False,
    tags: list[str] | None = None,
    only_errors: bool = False,
    quiet: bool = False,
    show_fix: bool = False,
) -> int:
    """
    Report on the compatibility of the tools in the pyproject.toml file.

    Args:
        file_path (Path, optional): The path to the pyproject.toml file. Defaults to "pyproject.toml".
        config_as_dict (Optional[dict[str, models.CliToolConfig]], optional): A dictionary of tool names and CliToolConfig objects. Defaults to None.
        exit_code_on_failure (bool, optional): If True, exit with return value of 1 if validation fails. Defaults to True.
        file_format (str, optional): The format of the output. Defaults to "table".
        no_cache (bool, optional): If True, don't use the cache. Defaults to False.
        tags (Optional[list[str]], optional): Only check tools with these tags. Defaults to None.
        only_errors (bool, optional): Only show errors. Defaults to False.
        quiet (bool, optional): If True, suppress all output. Defaults to False.
        show_fix (bool, optional): If True, print install hints for failed tools. Defaults to False.

    Returns:
        int: The exit code.
    """
    if tags is None:
        tags = []
    if not file_format:
        file_format = "table"

    if config_as_dict:
        results = process_tools(config_as_dict, no_cache, tags, disable_progress_bar=file_format != "table")
    elif file_path:
        # Handle config file searching.
        if not file_path.exists():
            one_up = ".." / file_path
            if one_up.exists():
                file_path = one_up
        cli_tools = config_reader.read_config(file_path)
        if not cli_tools and file_format == "pretty":
            cli_tools = get_default_tools()
        results = process_tools(cli_tools, no_cache, tags, disable_progress_bar=file_format != "table")
    else:
        raise TypeError("Must provide either file_path or config_as_dict.")

    success_and_failure = len(results)
    # Remove success, no action needed.
    if only_errors:
        results = [result for result in results if result.is_problem()]

    failed = policy.apply_policy(results)

    if file_format == "quiet" or quiet:
        logger.debug("Quiet mode enabled, suppressing UI output. If you want no output at all, don't select --verbose")
    elif file_format == "json":
        print(json.dumps([result.__dict__ for result in results], indent=4, default=json_utils.custom_json_serializer))
    elif file_format == "json-compact":
        print(json.dumps([result.__dict__ for result in results], default=json_utils.custom_json_serializer))
    elif file_format == "xml":
        print("<results>")
        for result in results:
            print("  <result>")
            for key, value in result.__dict__.items():
                print(f"    <{key}>{value}</{key}>")
            print("  </result>")
        print("</results>")
    elif file_format == "table":
        table = pretty_print_results(results, truncate_long_versions=True, include_docs=False)
        print(table)
        if not quiet:
            summary = summarize_failures(results)
            if summary:
                print(summary)
            if show_fix:
                install_hints = get_install_hints(results)
                if install_hints:
                    print("Install hints:")
                    for hint in install_hints:
                        print(f"- {hint}")
                elif failed:
                    print("No install hints configured for failed tools.")
    elif file_format == "csv":
        print(
            "tool,desired_version,is_available,is_snapshot,found_version,parsed_version,is_compatible,is_broken,last_modified"
        )
        for result in results:
            print(
                f"{result.tool},{result.desired_version},{result.is_available},{result.is_snapshot},{result.found_version},{result.parsed_version},{result.is_compatible},{result.is_broken},{result.last_modified}"
            )
    elif file_format == "html":
        table = pretty_print_results(results, truncate_long_versions=False, include_docs=True)
        print(table.get_html_string())
    elif file_format == "pretty":
        pretty_print_results_pretty(results)
        if not quiet:
            no_color = bool(os.environ.get("NO_COLOR") or os.environ.get("CI"))
            red = "" if no_color else colorama.Fore.RED
            green = "" if no_color else colorama.Fore.GREEN
            reset = "" if no_color else colorama.Style.RESET_ALL
            failures = [r for r in results if r.is_problem()]
            if failures:
                print(f"{red}{len(failures)} tools failed validation!{reset}")
            else:
                print(f"{green}All tools passed validation.{reset}")
            if show_fix:
                install_hints = get_install_hints(results)
                if install_hints:
                    print("\nInstall hints:")
                    for hint in install_hints:
                        print(f"- {hint}")
    else:
        print(
            f"Unknown file format: {file_format}, defaulting to table output. Supported formats: json, json-compact, xml, table, csv."
        )
        table = pretty_print_results(results, truncate_long_versions=True, include_docs=False)
        print(table)

    if only_errors and success_and_failure > 0 and len(results) == 0:
        if not quiet:
            print("No errors found, all tools meet version policy.")
        return 0
    if failed and exit_code_on_failure and file_format == "table":
        if not quiet:
            print("Did not pass validation, failing with return value of 1.")
        return 1
    return 0


def pretty_print_results(
    results: list[models.ToolCheckResult], truncate_long_versions: bool, include_docs: bool
) -> Union[PrettyTable, ColorTable]:
    """
    Pretty print the results of the validation.

    Args:
        results (list[models.ToolCheckResult]): A list of ToolCheckResult objects.
        truncate_long_versions (bool): If True, truncate long versions. Defaults to False.
        include_docs (bool): If True, include install command and install docs. Defaults to False.

    Returns:
        Union[PrettyTable, ColorTable]: A PrettyTable or ColorTable object.
    """
    if os.environ.get("NO_COLOR") or os.environ.get("CI"):
        table = PrettyTable()
    else:
        table = ColorTable(theme=Themes.OCEAN)
    table.field_names = ["Tool", "Found", "Parsed", "Desired", "Status", "Modified"]
    if include_docs:
        table.field_names.append("Install Command")
        table.field_names.append("Install Docs")

    all_rows: list[list[str]] = []

    for result in results:
        if truncate_long_versions:
            found_version = result.found_version[0:25].strip() if result.found_version else ""
        else:
            found_version = result.found_version or ""

        try:
            last_modified = result.last_modified.strftime("%m/%d/%y") if result.last_modified else ""
        except ValueError:
            last_modified = str(result.last_modified)
        row_data = [
            result.tool,
            found_version or "",
            result.parsed_version if result.parsed_version else "",
            result.desired_version or "",
            # "Yes" if result.is_compatible == "Compatible" else result.is_compatible,
            result.status() or "",
            last_modified,
        ]
        if include_docs:
            row_data.append(result.tool_config.install_command or "")
            row_data.append(result.tool_config.install_docs or "")
        row_transformed = []
        for datum in row_data:
            if result.is_problem():
                transformed = f"{colorama.Fore.RED}{datum}{colorama.Style.RESET_ALL}"
            else:
                transformed = str(datum)
            row_transformed.append(transformed)
        all_rows.append(row_transformed)

    table.add_rows(sorted(all_rows, key=lambda x: x[0]))

    return table


def summarize_failures(results: list[models.ToolCheckResult]) -> str | None:
    """
    Build a short, human-readable summary of failed tool checks.

    Args:
        results (list[models.ToolCheckResult]): The results to summarize.

    Returns:
        str | None: A summary line, or None when there are no failures.
    """
    failures = sorted((result for result in results if result.is_problem()), key=lambda result: result.tool.lower())
    if not failures:
        return None
    tool_label = "tool" if len(failures) == 1 else "tools"
    details = ", ".join(f"{result.tool} ({result.failure_reason()})" for result in failures)
    return f"{len(failures)} {tool_label} failed: {details}"


def get_install_hints(results: list[models.ToolCheckResult]) -> list[str]:
    """
    Collect install hints for failed tools.

    Args:
        results (list[models.ToolCheckResult]): The results to inspect.

    Returns:
        list[str]: Human-readable install hints for failed tools that define them.
    """
    hints: list[str] = []
    failures = sorted((result for result in results if result.is_problem()), key=lambda result: result.tool.lower())
    for result in failures:
        hint_parts = [result.tool]
        if result.tool_config.install_command:
            hint_parts.append(f"run `{result.tool_config.install_command}`")
        if result.tool_config.install_docs:
            hint_parts.append(f"see `{result.tool_config.install_docs}`")
        if len(hint_parts) > 1:
            hints.append(": ".join([hint_parts[0], "; ".join(hint_parts[1:])]))
    return hints


def should_show_progress_bar(cli_tools) -> bool | None:
    """
    Determine if a progress bar should be shown.

    Args:
        cli_tools: A dictionary of tool names and CliToolConfig objects.

    Returns:
        Optional[bool]: True if the progress bar should be shown, False if it should be hidden, or None if it can't be determined
    """
    disable = len(cli_tools) < 5 or os.environ.get("CI") or os.environ.get("NO_COLOR")
    return True if disable else None


def detect_language() -> str:
    """Detect the primary language of the project."""
    cwd = Path.cwd()
    if (cwd / "pyproject.toml").exists() or (cwd / "requirements.txt").exists() or (cwd / "setup.py").exists():
        return "python"
    if (cwd / "pom.xml").exists() or (cwd / "build.gradle").exists() or (cwd / "build.gradle.kts").exists():
        return "java"
    if (cwd / "go.mod").exists():
        return "go"
    if (cwd / "Cargo.toml").exists():
        return "rust"
    if (cwd / "package.json").exists():
        return "javascript"
    return "default"


def get_logo(lang: str, no_color: bool) -> list[str]:
    """Get the ANSI logo for the detected language."""
    cyan = "" if no_color else colorama.Fore.CYAN
    yellow = "" if no_color else colorama.Fore.YELLOW
    blue = "" if no_color else colorama.Fore.BLUE
    red = "" if no_color else colorama.Fore.RED
    green = "" if no_color else colorama.Fore.GREEN
    # magenta = "" if no_color else colorama.Fore.MAGENTA
    reset = "" if no_color else colorama.Style.RESET_ALL

    logos = {
        "python": [
            f"{blue}   _____  {reset}",
            f"{blue}  /  _  \\ {reset}",
            f"{blue} /  / \\  \\{reset}",
            f"{yellow}|  |   |  |{reset}",
            f"{yellow} \\  \\_/  /{reset}",
            f"{yellow}  \\_____/ {reset}",
        ],
        "java": [
            f"{red}   _     {reset}",
            f"{red}  (_)    {reset}",
            f"{red}  | |    {reset}",
            f"{red}  | |    {reset}",
            f"{yellow} /___\\   {reset}",
            f"{yellow}(_____)  {reset}",
        ],
        "go": [
            f"{cyan}  ____   {reset}",
            f"{cyan} /    \\  {reset}",
            f"{cyan}|  go  | {reset}",
            f"{cyan} \\____/  {reset}",
            f"{cyan}  |  |   {reset}",
            f"{cyan}  |__|   {reset}",
        ],
        "rust": [
            f"{red}  ____   {reset}",
            f"{red} /    \\  {reset}",
            f"{red}| rust | {reset}",
            f"{red} \\____/  {reset}",
            f"{red}  |  |   {reset}",
            f"{red}  |__|   {reset}",
        ],
        "javascript": [
            f"{yellow}  _____  {reset}",
            f"{yellow} |     | {reset}",
            f"{yellow} |  JS | {reset}",
            f"{yellow} |     | {reset}",
            f"{yellow} |_____| {reset}",
            f"{yellow}         {reset}",
        ],
        "default": [
            f"{green}  _____  {reset}",
            f"{green} /     \\ {reset}",
            f"{green}| AUDIT |{reset}",
            f"{green} \\_____/ {reset}",
            f"{green}  |   |  {reset}",
            f"{green}  |___|  {reset}",
        ],
    }
    return logos.get(lang, logos["default"])


def pretty_print_results_pretty(results: list[models.ToolCheckResult]):
    """Pretty print results in a neofetch-style layout."""
    no_color = bool(os.environ.get("NO_COLOR") or os.environ.get("CI"))
    lang = detect_language()
    logo = get_logo(lang, no_color)
    logo_width = 12

    bold = "" if no_color else colorama.Style.BRIGHT
    reset = "" if no_color else colorama.Style.RESET_ALL
    red = "" if no_color else colorama.Fore.RED
    green = "" if no_color else colorama.Fore.GREEN
    yellow = "" if no_color else colorama.Fore.YELLOW

    # System info-like header
    import platform

    from cli_tool_audit.__about__ import __version__

    node_name = platform.node()
    header = f"{bold}{yellow}cli_tool_audit{reset} @ {bold}{yellow}{node_name}{reset}"
    info_lines = [
        header,
        f"{'-' * (len(node_name) + 17)}",
        f"{bold}Version:{reset} {__version__}",
        f"{bold}OS:{reset}      {platform.system()} {platform.release()}",
        f"{bold}Language:{reset}{lang.capitalize()}",
        "",
    ]

    # Tool results
    for result in sorted(results, key=lambda x: x.tool):
        status_char = f"{red}*{reset}" if result.is_problem() else " "
        found_version = result.found_version or "N/A"
        # Only take first line of version and strip it
        found_version = found_version.split("\n")[0].strip()
        if len(found_version) > 40:
            found_version = found_version[:37] + "..."

        tool_color = red if result.is_problem() else green
        info_lines.append(f"{status_char} {tool_color}{result.tool:12}{reset}: {found_version}")

    # Print logo and info side by side
    max_lines = max(len(logo), len(info_lines))
    for i in range(max_lines):
        # We need to handle ANSI codes for width calculation if we wanted to be perfect,
        # but since we know our logos, we can just use a fixed width.
        # The logos are about 10-12 chars wide excluding ANSI codes.
        raw_logo = logo[i] if i < len(logo) else ""

        # Calculate padding: logo is ~10 chars, let's use 15 for space
        # Since raw_logo has ANSI codes, len(raw_logo) is larger than visible width.
        # But we can just use a fixed padding for the info part.

        line_info = info_lines[i] if i < len(info_lines) else ""

        if i < len(logo):
            print(f" {raw_logo}   {line_info}")
        else:
            print(f" {' ' * logo_width}   {line_info}")
    print()


if __name__ == "__main__":
    report_from_pyproject_toml()
