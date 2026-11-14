#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

hugo --source "$repo_root/landing" --minify --gc

# Preserve the existing pdoc URLs previously served by GitHub Pages.
mkdir -p "$repo_root/landing/public/cli_tool_audit"
cp -R "$repo_root/docs/cli_tool_audit/." "$repo_root/landing/public/cli_tool_audit/"
