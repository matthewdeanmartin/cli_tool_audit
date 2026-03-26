"""
cli_tool_audit GUI — tkinter application.

Layout: sidebar (left) | main panel (centre) | help panel (right)

All heavy I/O runs in background threads via _BackgroundRunner so the
UI stays responsive.  The GUI never reads config or calls tools directly;
it delegates to the existing CLI modules.
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Literal

# ── Colour palette (Catppuccin Mocha inspired) ─────────────────────
_CLR_OK = "#22c55e"
_CLR_WARN = "#eab308"
_CLR_ERR = "#ef4444"
_CLR_DIM = "#9ca3af"
_CLR_BG = "#1e1e2e"
_CLR_BG_ALT = "#252536"
_CLR_FG = "#cdd6f4"
_CLR_ACCENT = "#89b4fa"
_CLR_SIDEBAR = "#181825"
_CLR_BTN = "#313244"
_CLR_BTN_ACTIVE = "#45475a"
_CLR_HELP_BG = "#1a1a2e"

_FONT_UI = ("Segoe UI", 11)
_FONT_UI_BOLD = ("Segoe UI", 11, "bold")
_FONT_HEADING = ("Segoe UI", 14, "bold")
_FONT_MONO = ("Consolas", 10)
_FONT_MONO_SMALL = ("Consolas", 9)
_FONT_HELP_HEADING = ("Segoe UI", 12, "bold")
_FONT_HELP = ("Segoe UI", 10)

_MIN_WIDTH = 1280
_MIN_HEIGHT = 720


# ── Background runner ───────────────────────────────────────────────


class _BackgroundRunner:
    """Run a callable off the UI thread and post results back via root.after."""

    def __init__(self, root: tk.Tk):
        self._root = root

    def run(self, func, *, args=(), on_success=None, on_error=None):
        def _worker():
            try:
                result = func(*args)
                if on_success:
                    self._root.after(0, on_success, result)
            except Exception as exc:  # noqa: BLE001
                if on_error:
                    self._root.after(0, on_error, exc)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()


# ── Reusable widget helpers ─────────────────────────────────────────


def _make_tree(parent, columns, height=18, show_headings=True):
    """Create a themed treeview with scrollbar and colour tags."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Dark.Treeview",
        background=_CLR_BG_ALT,
        foreground=_CLR_FG,
        fieldbackground=_CLR_BG_ALT,
        font=_FONT_MONO,
        rowheight=26,
    )
    style.configure(
        "Dark.Treeview.Heading",
        background=_CLR_BTN,
        foreground=_CLR_ACCENT,
        font=_FONT_UI_BOLD,
    )
    style.map("Dark.Treeview", background=[("selected", _CLR_BTN_ACTIVE)])

    frame = tk.Frame(parent, bg=_CLR_BG)
    show: Literal["tree", "headings", "tree headings", ""] = "headings" if show_headings else "tree"
    tree = ttk.Treeview(frame, columns=columns, show=show, height=height, style="Dark.Treeview")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=140, minwidth=80)

    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    tree.tag_configure("ok", foreground=_CLR_OK)
    tree.tag_configure("warn", foreground=_CLR_WARN)
    tree.tag_configure("error", foreground=_CLR_ERR)
    tree.tag_configure("dim", foreground=_CLR_DIM)

    return frame, tree


def _make_output(parent, height=12):
    """Create a read-only scrolled text area."""
    frame = tk.Frame(parent, bg=_CLR_BG)
    text = tk.Text(
        frame,
        height=height,
        bg=_CLR_BG_ALT,
        fg=_CLR_FG,
        font=_FONT_MONO,
        insertbackground=_CLR_FG,
        relief=tk.FLAT,
        wrap=tk.WORD,
        padx=10,
        pady=8,
    )
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
    text.configure(yscrollcommand=scrollbar.set, state=tk.DISABLED)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    return frame, text


def _output_set(text_widget, content):
    """Replace content of a read-only text widget. No-ops if widget was destroyed."""
    try:
        if not text_widget.winfo_exists():
            return
    except tk.TclError:
        return
    text_widget.configure(state=tk.NORMAL)
    text_widget.delete("1.0", tk.END)
    text_widget.insert("1.0", content)
    text_widget.configure(state=tk.DISABLED)


def _make_toolbar(parent):
    """Create a horizontal button bar."""
    bar = tk.Frame(parent, bg=_CLR_BG)
    return bar


def _toolbar_btn(bar, text, command, width=16):
    """Create a themed button inside a toolbar."""
    btn = tk.Button(
        bar,
        text=text,
        command=command,
        bg=_CLR_BTN,
        fg=_CLR_FG,
        activebackground=_CLR_BTN_ACTIVE,
        activeforeground=_CLR_FG,
        font=_FONT_UI,
        relief=tk.FLAT,
        cursor="hand2",
        width=width,
        padx=8,
        pady=4,
    )
    btn.pack(side=tk.LEFT, padx=4, pady=4)
    return btn


# ── Help / cheat-sheet content ──────────────────────────────────────

_HELP_TEXTS: dict[str, str] = {
    "audit": """\
AUDIT

Run the tool audit against your
pyproject.toml configuration.

Config format (pyproject.toml):
  [tool.cli-tools]
  ruff = {name="ruff",
          version=">=0.1.0",
          schema="semver"}

Columns:
  Tool      - executable name
  Found     - raw --version output
  Parsed    - cleaned version
  Desired   - version spec from config
  Status    - OK / Not Found / etc.
  Modified  - last modified date

Filters:
  Tags      - only check matching tags
  Only Errors - hide passing tools

Tip: use --fix in CLI to see install
hints for failing tools.
""",
    "freeze": """\
FREEZE

Capture the current version of tools
and generate a [tool.cli-tools] config
snippet.

Three modes:
  1. Explicit tool list
     Type tool names separated by spaces.

  2. From Makefile
     Scans your Makefile for recipe
     commands and snapshots versions
     of tools found on PATH.

  3. From PATH by category
     Categories: python, node, java,
     rust, go, ruby, docker, cloud,
     build, git, lint, security

Output is a TOML snippet you can paste
into pyproject.toml.
""",
    "discover": """\
DISCOVER

Scan your project for CLI tool
references across:

  - Makefile / GNUmakefile
  - .github/workflows/*.yml
  - package.json scripts
  - pyproject.toml scripts
  - Dockerfile RUN lines
  - scripts/*.sh
  - .pre-commit-config.yaml

Each tool shows which files
reference it.

Use "Generate Config" to produce
a freeze config for all discovered
tools.
""",
    "single": """\
SINGLE TOOL CHECK

Audit one tool without a config file.

Fields:
  Tool name  - the executable (required)
  Version    - desired version spec
  Schema     - semver, snapshot,
               pep440, or existence
  Switch     - version flag override
               (default: --version)

Schemas:
  semver     - semantic versioning
               supports >=, ^, ~, *
  snapshot   - exact full output match
  pep440     - Python PEP 440 rules
  existence  - just check it exists
""",
    "config": """\
CONFIGURATION

Manage tool entries in your
pyproject.toml config file.

Operations:
  Read   - list all tool configs
  Create - add a new tool entry
  Update - modify an existing entry
  Delete - remove a tool entry

Config lives under [tool.cli-tools]
in your pyproject.toml file.

Each entry supports:
  name, version, version_switch,
  schema, if_os, tags,
  install_command, install_docs
""",
    "welcome": """\
CLI TOOL AUDIT

Audit CLI tools for existence and
correct version numbers.

Getting started:
  1. Click "Audit" to check tools
     defined in pyproject.toml
  2. Click "Discover" to find tools
     referenced in your project
  3. Click "Freeze" to snapshot
     current tool versions

Quick CLI equivalents:
  cli_tool_audit audit
  cli_tool_audit discover
  cli_tool_audit freeze python ruff
  cli_tool_audit single ruff
  cli_tool_audit read
  cli_tool_audit create ruff
              --version ">=0.1.0"
              --schema semver

Keyboard shortcuts:
  Ctrl+Q  - Quit
  F5      - Refresh current panel
""",
}


# ── Base panel ──────────────────────────────────────────────────────


class _BasePanel(tk.Frame):
    """Base class for all content panels."""

    def __init__(self, parent, runner: _BackgroundRunner, status_var: tk.StringVar):
        super().__init__(parent, bg=_CLR_BG)
        self._runner = runner
        self._status = status_var

    def _alive(self) -> bool:
        """Return False if this panel has been destroyed (user switched panels)."""
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False


# ── Audit panel ─────────────────────────────────────────────────────


class AuditPanel(_BasePanel):
    """Run audit against pyproject.toml and display results."""

    def __init__(self, parent, runner, status_var):
        super().__init__(parent, runner, status_var)
        self._config_path = tk.StringVar(value="pyproject.toml")

        # Toolbar
        toolbar = _make_toolbar(self)
        toolbar.pack(fill=tk.X, padx=8, pady=(8, 0))

        _toolbar_btn(toolbar, "Run Audit", self._run_audit)
        _toolbar_btn(toolbar, "Only Errors", self._run_audit_errors)

        tk.Label(toolbar, text="Config:", bg=_CLR_BG, fg=_CLR_DIM, font=_FONT_UI).pack(side=tk.LEFT, padx=(16, 4))
        entry = tk.Entry(
            toolbar,
            textvariable=self._config_path,
            bg=_CLR_BG_ALT,
            fg=_CLR_FG,
            font=_FONT_MONO,
            insertbackground=_CLR_FG,
            relief=tk.FLAT,
            width=30,
        )
        entry.pack(side=tk.LEFT, padx=4)
        _toolbar_btn(toolbar, "Browse...", self._browse, width=10)

        # Results tree
        cols = ("Tool", "Found", "Parsed", "Desired", "Status", "Modified")
        tree_frame, self._tree = _make_tree(self, cols, height=22)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._tree.column("Tool", width=160)
        self._tree.column("Found", width=200)
        self._tree.column("Parsed", width=120)
        self._tree.column("Desired", width=120)
        self._tree.column("Status", width=140)
        self._tree.column("Modified", width=100)

        # Summary
        self._summary_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self._summary_var, bg=_CLR_BG, fg=_CLR_WARN, font=_FONT_UI, anchor=tk.W).pack(
            fill=tk.X, padx=12, pady=(0, 8)
        )

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select config file",
            filetypes=[("TOML files", "*.toml"), ("All files", "*.*")],
        )
        if path:
            self._config_path.set(path)

    def _run_audit(self):
        self._do_audit(only_errors=False)

    def _run_audit_errors(self):
        self._do_audit(only_errors=True)

    def _do_audit(self, only_errors=False):
        self._status.set("Running audit...")
        self._tree.delete(*self._tree.get_children())
        self._summary_var.set("")
        config_path = self._config_path.get()
        self._runner.run(
            self._fetch,
            args=(config_path,),
            on_success=lambda results: self._display(results, only_errors),
            on_error=self._on_error,
        )

    @staticmethod
    def _fetch(config_path):
        from cli_tool_audit.views import validate

        return validate(Path(config_path), no_cache=False, disable_progress_bar=True)

    def _display(self, results, only_errors=False):
        if not self._alive():
            return
        self._tree.delete(*self._tree.get_children())
        if only_errors:
            results = [r for r in results if r.is_problem()]

        for result in sorted(results, key=lambda r: r.tool.lower()):
            found = (result.found_version or "")[:40]
            parsed = result.parsed_version or ""
            desired = result.desired_version or ""
            status = result.status() if hasattr(result, "status") else ""
            try:
                modified = result.last_modified.strftime("%m/%d/%y") if result.last_modified else ""
            except ValueError:
                modified = str(result.last_modified) if result.last_modified else ""

            tag = "error" if result.is_problem() else "ok"
            self._tree.insert("", tk.END, values=(result.tool, found, parsed, desired, status, modified), tags=(tag,))

        # Summary
        from cli_tool_audit.views import summarize_failures

        summary = summarize_failures(results)
        total = len(results)
        if summary:
            self._summary_var.set(f"{total} tools checked. {summary}")
        else:
            self._summary_var.set(f"{total} tools checked. All passing.")
        self._status.set(f"Audit complete — {total} tools checked.")

    def _on_error(self, exc):
        if not self._alive():
            return
        self._status.set("Audit failed.")
        messagebox.showerror("Audit Error", str(exc))


# ── Freeze panel ────────────────────────────────────────────────────


class FreezePanel(_BasePanel):
    """Freeze tool versions — manual list, from Makefile, or by PATH category."""

    def __init__(self, parent, runner, status_var):
        super().__init__(parent, runner, status_var)

        # Mode selector
        mode_frame = tk.Frame(self, bg=_CLR_BG)
        mode_frame.pack(fill=tk.X, padx=8, pady=(8, 0))
        self._mode = tk.StringVar(value="manual")
        for val, label in [("manual", "Tool List"), ("makefile", "From Makefile"), ("path", "From PATH")]:
            tk.Radiobutton(
                mode_frame,
                text=label,
                variable=self._mode,
                value=val,
                bg=_CLR_BG,
                fg=_CLR_FG,
                selectcolor=_CLR_BTN,
                activebackground=_CLR_BG,
                activeforeground=_CLR_ACCENT,
                font=_FONT_UI,
                command=self._on_mode_change,
            ).pack(side=tk.LEFT, padx=8)

        # Input area
        input_frame = tk.Frame(self, bg=_CLR_BG)
        input_frame.pack(fill=tk.X, padx=8, pady=4)

        tk.Label(input_frame, text="Tools:", bg=_CLR_BG, fg=_CLR_DIM, font=_FONT_UI).pack(side=tk.LEFT, padx=(0, 4))
        self._tools_entry = tk.Entry(
            input_frame,
            bg=_CLR_BG_ALT,
            fg=_CLR_FG,
            font=_FONT_MONO,
            insertbackground=_CLR_FG,
            relief=tk.FLAT,
            width=50,
        )
        self._tools_entry.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        self._tools_entry.insert(0, "python ruff mypy pytest")

        # Category dropdown for PATH mode
        self._category_frame = tk.Frame(input_frame, bg=_CLR_BG)
        tk.Label(self._category_frame, text="Category:", bg=_CLR_BG, fg=_CLR_DIM, font=_FONT_UI).pack(
            side=tk.LEFT, padx=(8, 4)
        )
        self._category_var = tk.StringVar(value="(all)")
        from cli_tool_audit.freeze import list_path_categories

        categories = ["(all)"] + list_path_categories()
        self._category_menu = ttk.Combobox(
            self._category_frame,
            textvariable=self._category_var,
            values=categories,
            state="readonly",
            width=14,
        )
        self._category_menu.pack(side=tk.LEFT, padx=4)

        # Toolbar
        toolbar = _make_toolbar(self)
        toolbar.pack(fill=tk.X, padx=8, pady=4)
        _toolbar_btn(toolbar, "Freeze", self._run_freeze)

        # Output
        output_frame, self._output = _make_output(self, height=22)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self._on_mode_change()

    def _on_mode_change(self):
        mode = self._mode.get()
        if mode == "path":
            self._category_frame.pack(side=tk.LEFT, padx=4)
            self._tools_entry.configure(state=tk.DISABLED)
        elif mode == "makefile":
            self._category_frame.pack_forget()
            self._tools_entry.configure(state=tk.DISABLED)
        else:
            self._category_frame.pack_forget()
            self._tools_entry.configure(state=tk.NORMAL)

    def _run_freeze(self):
        mode = self._mode.get()
        self._status.set("Freezing tool versions...")
        _output_set(self._output, "")
        self._runner.run(
            self._fetch,
            args=(mode, self._tools_entry.get(), self._category_var.get()),
            on_success=self._display,
            on_error=self._on_error,
        )

    @staticmethod
    def _fetch(mode, tools_text, category):
        import contextlib
        import io

        from cli_tool_audit import freeze, models

        buf = io.StringIO()
        if mode == "makefile":
            tool_names = freeze.infer_tools_from_makefile()
            if not tool_names:
                return "No tools discovered in Makefile (or none found on PATH)."
            header = f"# Discovered from Makefile: {', '.join(tool_names)}\n\n"
        elif mode == "path":
            cat = category if category != "(all)" else None
            tool_names = freeze.infer_tools_from_path(cat)
            if not tool_names:
                label = f"category '{cat}'" if cat else "any category"
                return f"No tools found on PATH for {label}."
            label = f"'{cat}'" if cat else "all categories"
            header = f"# Discovered on PATH ({label}): {', '.join(tool_names)}\n\n"
        else:
            tool_names = tools_text.split()
            if not tool_names:
                return "Enter tool names separated by spaces."
            header = ""

        with contextlib.redirect_stdout(buf):
            freeze.freeze_to_screen(tool_names, schema=models.SchemaType.SNAPSHOT)
        return header + buf.getvalue()

    def _display(self, output):
        if not self._alive():
            return
        _output_set(self._output, output)
        self._status.set("Freeze complete.")

    def _on_error(self, exc):
        if not self._alive():
            return
        self._status.set("Freeze failed.")
        messagebox.showerror("Freeze Error", str(exc))


# ── Discover panel ──────────────────────────────────────────────────


class DiscoverPanel(_BasePanel):
    """Scan project files for CLI tool references."""

    def __init__(self, parent, runner, status_var):
        super().__init__(parent, runner, status_var)

        toolbar = _make_toolbar(self)
        toolbar.pack(fill=tk.X, padx=8, pady=(8, 0))

        tk.Label(toolbar, text="Project root:", bg=_CLR_BG, fg=_CLR_DIM, font=_FONT_UI).pack(side=tk.LEFT, padx=(0, 4))
        self._root_var = tk.StringVar(value=str(Path.cwd()))
        entry = tk.Entry(
            toolbar,
            textvariable=self._root_var,
            bg=_CLR_BG_ALT,
            fg=_CLR_FG,
            font=_FONT_MONO,
            insertbackground=_CLR_FG,
            relief=tk.FLAT,
            width=40,
        )
        entry.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        _toolbar_btn(toolbar, "Browse...", self._browse, width=10)
        _toolbar_btn(toolbar, "Scan", self._run_discover)
        _toolbar_btn(toolbar, "Generate Config", self._run_generate)

        # Results tree
        cols = ("Tool", "Found In")
        tree_frame, self._tree = _make_tree(self, cols, height=16)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._tree.column("Tool", width=220)
        self._tree.column("Found In", width=500)

        # Config output (shown when Generate is clicked)
        output_frame, self._output = _make_output(self, height=10)
        output_frame.pack(fill=tk.BOTH, padx=8, pady=(0, 8))

        self._last_sources: dict = {}

    def _browse(self):
        path = filedialog.askdirectory(title="Select project root")
        if path:
            self._root_var.set(path)

    def _run_discover(self):
        self._status.set("Scanning for tool references...")
        self._tree.delete(*self._tree.get_children())
        _output_set(self._output, "")
        self._runner.run(
            self._fetch_discover,
            args=(self._root_var.get(),),
            on_success=self._display_discover,
            on_error=self._on_error,
        )

    def _run_generate(self):
        if not self._last_sources:
            messagebox.showinfo("Discover First", "Run a scan first, then generate config.")
            return
        self._status.set("Generating freeze config...")
        tool_names = list(self._last_sources.keys())
        self._runner.run(
            self._fetch_generate,
            args=(tool_names,),
            on_success=self._display_generate,
            on_error=self._on_error,
        )

    @staticmethod
    def _fetch_discover(root_path):
        from cli_tool_audit.discover import discover_tools

        return discover_tools(Path(root_path))

    @staticmethod
    def _fetch_generate(tool_names):
        import contextlib
        import io

        from cli_tool_audit import freeze, models

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            freeze.freeze_to_screen(tool_names, schema=models.SchemaType.SNAPSHOT)
        return buf.getvalue()

    def _display_discover(self, sources):
        if not self._alive():
            return
        self._tree.delete(*self._tree.get_children())
        self._last_sources = sources
        for tool, locs in sources.items():
            self._tree.insert("", tk.END, values=(tool, ", ".join(locs)), tags=("ok",))
        count = len(sources)
        self._status.set(f"Discovered {count} tool(s).")

    def _display_generate(self, output):
        if not self._alive():
            return
        _output_set(self._output, output)
        self._status.set("Config generated. Copy the TOML snippet above.")

    def _on_error(self, exc):
        if not self._alive():
            return
        self._status.set("Discover failed.")
        messagebox.showerror("Discover Error", str(exc))


# ── Single tool panel ───────────────────────────────────────────────


class SinglePanel(_BasePanel):
    """Audit a single tool without config file."""

    def __init__(self, parent, runner, status_var):
        super().__init__(parent, runner, status_var)

        # Form
        form = tk.Frame(self, bg=_CLR_BG)
        form.pack(fill=tk.X, padx=12, pady=(12, 4))

        row = 0
        self._entries: dict[str, Any] = {}
        for label_text, key, default, width in [
            ("Tool name:", "tool", "", 30),
            ("Version:", "version", "", 30),
            ("Switch:", "switch", "--version", 20),
        ]:
            tk.Label(form, text=label_text, bg=_CLR_BG, fg=_CLR_FG, font=_FONT_UI, anchor=tk.W).grid(
                row=row,
                column=0,
                sticky=tk.W,
                padx=(0, 8),
                pady=6,
            )
            var = tk.StringVar(value=default)
            entry = tk.Entry(
                form,
                textvariable=var,
                bg=_CLR_BG_ALT,
                fg=_CLR_FG,
                font=_FONT_MONO,
                insertbackground=_CLR_FG,
                relief=tk.FLAT,
                width=width,
            )
            entry.grid(row=row, column=1, sticky=tk.W, pady=6)
            self._entries[key] = var
            row += 1

        # Schema
        tk.Label(form, text="Schema:", bg=_CLR_BG, fg=_CLR_FG, font=_FONT_UI, anchor=tk.W).grid(
            row=row,
            column=0,
            sticky=tk.W,
            padx=(0, 8),
            pady=6,
        )
        self._schema_var = tk.StringVar(value="semver")
        schema_combo = ttk.Combobox(
            form,
            textvariable=self._schema_var,
            values=["semver", "snapshot", "pep440", "existence"],
            state="readonly",
            width=14,
        )
        schema_combo.grid(row=row, column=1, sticky=tk.W, pady=6)

        # Button
        toolbar = _make_toolbar(self)
        toolbar.pack(fill=tk.X, padx=8, pady=4)
        _toolbar_btn(toolbar, "Check Tool", self._run_check)

        # Output
        output_frame, self._output = _make_output(self, height=16)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    def _run_check(self):
        tool = self._entries["tool"].get().strip()
        if not tool:
            messagebox.showinfo("Missing", "Enter a tool name.")
            return
        self._status.set(f"Checking {tool}...")
        _output_set(self._output, "")
        self._runner.run(
            self._fetch,
            args=(tool, self._entries["version"].get(), self._entries["switch"].get(), self._schema_var.get()),
            on_success=self._display,
            on_error=self._on_error,
        )

    @staticmethod
    def _fetch(tool, version, switch, schema):
        import contextlib
        import io

        from cli_tool_audit import models, views

        config = models.CliToolConfig(
            name=tool,
            version=version or None,
            version_switch=switch or None,
            schema=schema,
        )
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            views.report_from_pyproject_toml(
                file_path=None,
                config_as_dict={tool: config},
                exit_code_on_failure=False,
                file_format="table",
                no_cache=False,
                tags=None,
                only_errors=False,
            )
        return buf.getvalue()

    def _display(self, output):
        if not self._alive():
            return
        _output_set(self._output, output)
        self._status.set("Check complete.")

    def _on_error(self, exc):
        if not self._alive():
            return
        self._status.set("Check failed.")
        messagebox.showerror("Check Error", str(exc))


# ── Config panel ────────────────────────────────────────────────────


class ConfigPanel(_BasePanel):
    """Read / Create / Update / Delete tool configurations."""

    def __init__(self, parent, runner, status_var):
        super().__init__(parent, runner, status_var)

        self._config_path = tk.StringVar(value="pyproject.toml")

        # Top bar
        top = tk.Frame(self, bg=_CLR_BG)
        top.pack(fill=tk.X, padx=8, pady=(8, 0))
        tk.Label(top, text="Config:", bg=_CLR_BG, fg=_CLR_DIM, font=_FONT_UI).pack(side=tk.LEFT, padx=(0, 4))
        tk.Entry(
            top,
            textvariable=self._config_path,
            bg=_CLR_BG_ALT,
            fg=_CLR_FG,
            font=_FONT_MONO,
            insertbackground=_CLR_FG,
            relief=tk.FLAT,
            width=30,
        ).pack(side=tk.LEFT, padx=4)
        _toolbar_btn(top, "Browse...", self._browse, width=10)
        _toolbar_btn(top, "Read Config", self._read_config)

        # Output
        output_frame, self._output = _make_output(self, height=26)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select config file",
            filetypes=[("TOML files", "*.toml"), ("All files", "*.*")],
        )
        if path:
            self._config_path.set(path)

    def _read_config(self):
        self._status.set("Reading configuration...")
        _output_set(self._output, "")
        self._runner.run(
            self._fetch,
            args=(self._config_path.get(),),
            on_success=self._display,
            on_error=self._on_error,
        )

    @staticmethod
    def _fetch(config_path):
        import contextlib
        import io

        from cli_tool_audit import config_manager

        buf = io.StringIO()
        manager = config_manager.ConfigManager(Path(config_path))
        manager.read_config()
        with contextlib.redirect_stdout(buf):
            for tool, config in manager.tools.items():
                print(f"{tool}")
                for key, value in vars(config).items():
                    if value is not None:
                        print(f"  {key}: {value}")
                print()
        return buf.getvalue()

    def _display(self, output):
        if not self._alive():
            return
        _output_set(self._output, output or "(No tools configured)")
        self._status.set("Configuration loaded.")

    def _on_error(self, exc):
        if not self._alive():
            return
        self._status.set("Config read failed.")
        messagebox.showerror("Config Error", str(exc))


# ── Welcome panel ───────────────────────────────────────────────────


class WelcomePanel(_BasePanel):
    """Landing page with overview."""

    def __init__(self, parent, runner, status_var):
        super().__init__(parent, runner, status_var)

        # Title
        tk.Label(
            self,
            text="CLI Tool Audit",
            bg=_CLR_BG,
            fg=_CLR_ACCENT,
            font=("Segoe UI", 24, "bold"),
        ).pack(pady=(40, 8))
        tk.Label(
            self,
            text="Audit CLI tools for existence and correct version numbers",
            bg=_CLR_BG,
            fg=_CLR_DIM,
            font=("Segoe UI", 13),
        ).pack(pady=(0, 24))

        # Quick-start cards
        cards_frame = tk.Frame(self, bg=_CLR_BG)
        cards_frame.pack(pady=16)

        cards = [
            ("Audit", "Check tools against\npyproject.toml config", _CLR_OK),
            ("Discover", "Find tool references\nacross project files", _CLR_ACCENT),
            ("Freeze", "Snapshot current\ntool versions", _CLR_WARN),
            ("Single", "Quick-check one\ntool by name", _CLR_DIM),
        ]
        for title, desc, color in cards:
            card = tk.Frame(cards_frame, bg=_CLR_BG_ALT, padx=20, pady=16)
            card.pack(side=tk.LEFT, padx=12)
            tk.Label(card, text=title, bg=_CLR_BG_ALT, fg=color, font=_FONT_HEADING).pack(anchor=tk.W)
            tk.Label(card, text=desc, bg=_CLR_BG_ALT, fg=_CLR_FG, font=_FONT_UI, justify=tk.LEFT).pack(
                anchor=tk.W,
                pady=(4, 0),
            )

        tk.Label(
            self,
            text="Select a command from the sidebar to get started.",
            bg=_CLR_BG,
            fg=_CLR_DIM,
            font=_FONT_UI,
        ).pack(pady=(24, 0))


# ── Main application ────────────────────────────────────────────────


class CliToolAuditApp:
    """Main application window."""

    def __init__(self):
        self._root = tk.Tk()
        self._root.title("CLI Tool Audit")
        self._root.configure(bg=_CLR_BG)
        self._root.minsize(_MIN_WIDTH, _MIN_HEIGHT)
        self._root.geometry(f"{_MIN_WIDTH}x{_MIN_HEIGHT}")

        self._status_var = tk.StringVar(value="Ready.")
        self._runner = _BackgroundRunner(self._root)
        self._current_panel: tk.Frame | None = None
        self._current_panel_name: str = ""
        self._sidebar_buttons: dict[str, tk.Button] = {}

        self._build_ui()
        self._bind_keys()
        self._show_panel("welcome")

    def _bind_keys(self):
        self._root.bind("<Control-q>", lambda _: self._root.destroy())
        self._root.bind("<F5>", lambda _: self._refresh())

    def _refresh(self):
        """Re-create the current panel to refresh its data."""
        if self._current_panel_name:
            self._show_panel(self._current_panel_name)

    def _build_ui(self):
        # Three-column layout: sidebar | main | help
        container = tk.Frame(self._root, bg=_CLR_BG)
        container.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar ──
        sidebar = tk.Frame(container, bg=_CLR_SIDEBAR, width=180)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="Commands",
            bg=_CLR_SIDEBAR,
            fg=_CLR_ACCENT,
            font=_FONT_HEADING,
        ).pack(pady=(16, 12), padx=12, anchor=tk.W)

        items = [
            ("welcome", "Home"),
            ("audit", "Audit"),
            ("discover", "Discover"),
            ("freeze", "Freeze"),
            ("single", "Single Check"),
            ("config", "Config"),
        ]
        for key, label in items:
            btn = tk.Button(
                sidebar,
                text=f"  {label}",
                # mypy cannot infer lambda type in loop - this is a known limitation
                command=lambda k=key: self._show_panel(k),  # type: ignore[misc]
                bg=_CLR_SIDEBAR,
                fg=_CLR_FG,
                activebackground=_CLR_BTN_ACTIVE,
                activeforeground=_CLR_FG,
                font=_FONT_UI,
                relief=tk.FLAT,
                anchor=tk.W,
                cursor="hand2",
                padx=12,
                pady=8,
            )
            btn.pack(fill=tk.X, padx=4, pady=1)
            self._sidebar_buttons[key] = btn

        # Version at bottom of sidebar
        from cli_tool_audit.__about__ import __version__

        tk.Label(
            sidebar,
            text=f"v{__version__}",
            bg=_CLR_SIDEBAR,
            fg=_CLR_DIM,
            font=_FONT_MONO_SMALL,
        ).pack(side=tk.BOTTOM, pady=8)

        # ── Main panel area ──
        self._main_area = tk.Frame(container, bg=_CLR_BG)
        self._main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── Help panel (right) ──
        help_frame = tk.Frame(container, bg=_CLR_HELP_BG, width=260)
        help_frame.pack(side=tk.RIGHT, fill=tk.Y)
        help_frame.pack_propagate(False)

        tk.Label(
            help_frame,
            text="Help",
            bg=_CLR_HELP_BG,
            fg=_CLR_ACCENT,
            font=_FONT_HELP_HEADING,
        ).pack(pady=(16, 8), padx=12, anchor=tk.W)

        self._help_text = tk.Text(
            help_frame,
            bg=_CLR_HELP_BG,
            fg=_CLR_FG,
            font=_FONT_HELP,
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=12,
            pady=8,
            state=tk.DISABLED,
            cursor="arrow",
            highlightthickness=0,
        )
        self._help_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 8))

        # ── Status bar ──
        status_bar = tk.Label(
            self._root,
            textvariable=self._status_var,
            bg=_CLR_SIDEBAR,
            fg=_CLR_DIM,
            font=_FONT_MONO_SMALL,
            anchor=tk.W,
            padx=12,
            pady=4,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _show_panel(self, name: str):
        """Destroy current panel and show the named one."""
        if self._current_panel:
            self._current_panel.destroy()

        self._current_panel_name = name

        # Update sidebar highlight
        for key, btn in self._sidebar_buttons.items():
            if key == name:
                btn.configure(bg=_CLR_BTN, fg=_CLR_ACCENT)
            else:
                btn.configure(bg=_CLR_SIDEBAR, fg=_CLR_FG)

        # Build panel
        builders = {
            "welcome": WelcomePanel,
            "audit": AuditPanel,
            "discover": DiscoverPanel,
            "freeze": FreezePanel,
            "single": SinglePanel,
            "config": ConfigPanel,
        }
        panel_cls = builders.get(name, WelcomePanel)
        self._current_panel = panel_cls(self._main_area, self._runner, self._status_var)
        self._current_panel.pack(fill=tk.BOTH, expand=True)

        # Update help text
        help_key = name if name in _HELP_TEXTS else "welcome"
        _output_set(self._help_text, _HELP_TEXTS[help_key])

    def run(self):
        """Start the tkinter main loop."""
        self._root.mainloop()


def launch_gui():
    """Entry point for the GUI."""
    app = CliToolAuditApp()
    app.run()
    return 0
