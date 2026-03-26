Version 3.2.0
---

  2. Auto-discovery: cli_tool_audit discover

  A new subcommand that scans the current project for tool references across:
  - Makefile / GNUmakefile
  - .github/workflows/*.yml (uses: / run: lines)
  - package.json scripts
  - pyproject.toml scripts/build
  - Dockerfile RUN lines
  - scripts/ shell scripts
  - .pre-commit-config.yaml

  Then it either reports what it found, or offers to write the config for you. This is the zero-effort onramp.
  

  4. Smarter default: run audit when invoked with no subcommand

  Currently running cli_tool_audit with no args says "No command specified. Auditing environment with pyproject.toml configuration." which is fine, but it audits without caching (no_cache=True). That's
  inconsistent with cli_tool_audit audit which uses caching. Just make the default behavior identical to audit.

 5. freeze should infer tools from PATH by category

  Running cli_tool_audit freeze python java make rustc requires knowing what you want. A better UX: cli_tool_audit
  freeze --from-makefile or cli_tool_audit freeze --from-path --category python that auto-discovers tools by type and
  snapshots them. Lower friction = more adoption.

  6. Better status messages on failure

  When a tool fails, the "Status" column shows things like "1.2.3 != >=1.5.0". That's cryptic for a new user. It should
  say something like "outdated (have 1.2.3, need >=1.5.0)" or at minimum emit a human-readable summary line at the end:
  "3 tools failed: mypy (outdated), docker (not found), node (broken)"



  8. subprocess.CalledProcessError currently marks tool as broken

  In audit_manager.py:408, if a tool returns non-zero on --version, it's marked is_broken=True. But many tools (e.g.,
  curl --version, git --version) return 0, while some older tools return non-zero. This causes false-positive "broken"
  results. The fix: capture stdout even on non-zero exit codes, and only mark broken if there's genuinely no version
  output at all.


 3. cli_tool_audit audit --fix — Print the install command when a tool is broken

  When a tool fails, the output currently shows a red row with a status like "Not Found". But CliToolConfig already has install_command and install_docs fields! They just aren't shown by default in the table.

  The --fix flag (or even just by default) could:
  - Print actionable install hints at the bottom: run: pipx install mypy / see: https://...
  - Or even: offer to run the install command (with --auto-fix confirmation)

  - Store in tool common ways to install common tools.

10. More prepopulated tools with unusal switches for getting version

