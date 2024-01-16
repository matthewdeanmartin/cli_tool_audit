set -e
cli_tool_audit --help
cli_tool_audit --version
cli_tool_audit read
cli_tool_audit freeze python pip
cli_tool_audit  create sometool --version 1.2.3 --version-switch="--version"
cli_tool_audit  update sometool --version 3.2.1 --version-switch="-v"
cli_tool_audit  delete sometool
cli_tool_audit --verbose --never-fail
cli_tool_audit --never-fail


#    only_check_existence: Optional[bool] = False
#    schema: Optional[str] = None
#    if_os: Optional[str] = None
#    version_stamp: Optional[str] = None
#    source: Optional[str] = None