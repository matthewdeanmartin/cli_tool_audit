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
from typing import Optional, Union

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
    tags: Optional[list[str]] = None,
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
    tags: Optional[list[str]] = None,
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


def report_from_pyproject_toml(
    file_path: Optional[Path] = Path("pyproject.toml"),
    config_as_dict: Optional[dict[str, models.CliToolConfig]] = None,
    exit_code_on_failure: bool = True,
    file_format: str = "table",
    no_cache: bool = False,
    tags: Optional[list[str]] = None,
    only_errors: bool = False,
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
        results = validate(file_path, no_cache=no_cache, tags=tags, disable_progress_bar=file_format != "table")
    else:
        raise TypeError("Must provide either file_path or config_as_dict.")

    success_and_failure = len(results)
    # Remove success, no action needed.
    if only_errors:
        results = [result for result in results if result.is_problem()]

    failed = policy.apply_policy(results)

    if file_format == "json":
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
    else:
        print(
            f"Unknown file format: {file_format}, defaulting to table output. Supported formats: json, json-compact, xml, table, csv."
        )
        table = pretty_print_results(results, truncate_long_versions=True, include_docs=False)
        print(table)

    if only_errors and success_and_failure > 0 and len(results) == 0:
        print("No errors found, all tools meet version policy.")
        return 0
    if failed and exit_code_on_failure and file_format == "table":
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


def should_show_progress_bar(cli_tools) -> Optional[bool]:
    disable = len(cli_tools) < 5 or os.environ.get("CI") or os.environ.get("NO_COLOR")
    return True if disable else None


if __name__ == "__main__":
    report_from_pyproject_toml()
