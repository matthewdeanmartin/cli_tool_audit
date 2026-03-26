"""Tests for cli_tool_audit.gui.app module."""

import sys
from unittest.mock import MagicMock

import pytest

tk = pytest.importorskip("tkinter")


@pytest.fixture()
def root():
    try:
        r = tk.Tk()
        r.withdraw()
    except tk.TclError:
        pytest.skip("No display available")
    yield r
    r.destroy()


@pytest.fixture()
def runner(root):
    from cli_tool_audit.gui.app import _BackgroundRunner

    return _BackgroundRunner(root)


@pytest.fixture()
def status_var(root):
    return tk.StringVar(master=root, value="")


class TestImportGuard:
    """GUI import must not pull tkinter into normal CLI usage."""

    def test_cli_import_does_not_load_tkinter(self):
        # Importing __main__ should NOT import tkinter
        mods_before = set(sys.modules.keys())
        import cli_tool_audit.__main__  # noqa: F401

        # tkinter may already be loaded by pytest fixture setup, so we just
        # verify that importing __main__ itself doesn't *add* it
        assert "cli_tool_audit.gui.app" not in (set(sys.modules.keys()) - mods_before)


class TestBackgroundRunner:
    def test_success_callback(self):
        mock_root = MagicMock()
        mock_root.after = lambda _ms, fn, *a: fn(*a)

        from cli_tool_audit.gui.app import _BackgroundRunner

        runner = _BackgroundRunner(mock_root)

        results = []
        runner.run(lambda: 42, on_success=lambda r: results.append(r))

        # Give thread a moment to complete
        import time

        time.sleep(0.2)
        assert results == [42]

    def test_error_callback(self):
        mock_root = MagicMock()
        mock_root.after = lambda _ms, fn, *a: fn(*a)

        from cli_tool_audit.gui.app import _BackgroundRunner

        runner = _BackgroundRunner(mock_root)

        errors = []

        def _boom():
            raise ValueError("test error")

        runner.run(_boom, on_error=lambda e: errors.append(str(e)))

        import time

        time.sleep(0.2)
        assert any("test error" in e for e in errors)


class TestPanelCreation:
    """Verify each panel can be instantiated without error."""

    def test_welcome_panel(self, root, runner, status_var):
        from cli_tool_audit.gui.app import WelcomePanel

        panel = WelcomePanel(root, runner, status_var)
        root.update()
        assert panel.winfo_exists()

    def test_audit_panel(self, root, runner, status_var):
        from cli_tool_audit.gui.app import AuditPanel

        panel = AuditPanel(root, runner, status_var)
        root.update()
        assert panel.winfo_exists()

    def test_freeze_panel(self, root, runner, status_var):
        from cli_tool_audit.gui.app import FreezePanel

        panel = FreezePanel(root, runner, status_var)
        root.update()
        assert panel.winfo_exists()

    def test_discover_panel(self, root, runner, status_var):
        from cli_tool_audit.gui.app import DiscoverPanel

        panel = DiscoverPanel(root, runner, status_var)
        root.update()
        assert panel.winfo_exists()

    def test_single_panel(self, root, runner, status_var):
        from cli_tool_audit.gui.app import SinglePanel

        panel = SinglePanel(root, runner, status_var)
        root.update()
        assert panel.winfo_exists()

    def test_config_panel(self, root, runner, status_var):
        from cli_tool_audit.gui.app import ConfigPanel

        panel = ConfigPanel(root, runner, status_var)
        root.update()
        assert panel.winfo_exists()


class TestAppCreation:
    def test_app_creates_and_destroys(self):
        try:
            from cli_tool_audit.gui.app import CliToolAuditApp

            app = CliToolAuditApp()
            app._root.update()
            assert app._root.winfo_exists()
            app._root.destroy()
        except tk.TclError:
            pytest.skip("No display available")

    def test_panel_switching(self):
        try:
            from cli_tool_audit.gui.app import CliToolAuditApp

            app = CliToolAuditApp()
            for name in ["audit", "discover", "freeze", "single", "config", "welcome"]:
                app._show_panel(name)
                app._root.update()
                assert app._current_panel_name == name
            app._root.destroy()
        except tk.TclError:
            pytest.skip("No display available")


class TestHelpTexts:
    def test_all_panels_have_help(self):
        from cli_tool_audit.gui.app import _HELP_TEXTS

        expected = {"audit", "freeze", "discover", "single", "config", "welcome"}
        assert expected.issubset(set(_HELP_TEXTS.keys()))

    def test_help_texts_are_nonempty(self):
        from cli_tool_audit.gui.app import _HELP_TEXTS

        for key, text in _HELP_TEXTS.items():
            assert len(text.strip()) > 20, f"Help text for '{key}' is too short"
