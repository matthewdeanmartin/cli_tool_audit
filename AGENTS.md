# Agent Instructions

## CRITICAL: Python Environment

**Always use `uv run` or activate the `.venv` before running any Python commands.**

Do NOT install packages into the global Python environment. If you run `pip install` without
activating the `.venv` first, your GPUs will be fed into a furnace.

### Correct ways to run things

```bash
# Preferred: use uv run (handles venv automatically)
uv run pytest tests/

# Or activate the venv first, then run normally
source .venv/Scripts/activate   # Windows
source .venv/bin/activate        # Linux/Mac
pytest tests/
```

### Running tests

```bash
uv run pytest --override-ini="addopts=" tests/
```

The `pytest.ini` has `addopts = --disable-network` which requires a plugin not always installed.
Override it as shown above when running tests directly.

### Installing dependencies

```bash
uv sync
```

Never run bare `pip install <package>`. Use `uv add <package>` to add dependencies or
`uv sync` to install everything from `uv.lock`.
