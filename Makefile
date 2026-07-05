.EXPORT_ALL_VARIABLES:

# if you wrap everything in uv run, it runs slower.
ifeq ($(origin VIRTUAL_ENV),undefined)
    VENV := uv run
else
    VENV :=
endif

uv.lock: pyproject.toml
	@echo "Installing dependencies"
	@uv sync --all-extras

clean-pyc:
	@echo "Removing compiled files"



# tests can't be expected to pass if dependencies aren't installed.
# tests are often slow and linting is fast, so run tests on linted code.
test: uv.lock
	@echo "Running unit tests"
	# $(VENV) pytest --doctest-modules cli_tool_audit
	# $(VENV) python -m unittest discover
	$(VENV) pytest tests -vv -n 2 --cov=cli_tool_audit --cov-report=html --cov-fail-under 65 --cov-branch --cov-report=xml --junitxml=junit.xml -o junit_family=legacy --timeout=60 --session-timeout=600
	$(VENV) bash ./scripts/basic_checks.sh
#	$(VENV) bash basic_test_with_logging.sh

PYTEST_LLM_ARGS ?= --override-ini="addopts=" -q --tb=short --maxfail=1 --disable-warnings -r a

test-llm: uv.lock
	@echo "Running token-efficient tests"
	$(VENV) pytest tests $(PYTEST_LLM_ARGS)

test-llm-cov: uv.lock
	@echo "Running token-efficient tests with coverage"
	$(VENV) pytest tests $(PYTEST_LLM_ARGS) --cov=cli_tool_audit --cov-report=term-missing:skip-covered --cov-report=xml --cov-fail-under 35 --cov-branch

lint-llm:
	@echo "Running token-efficient lint checks"
	$(VENV) ruff check cli_tool_audit tests
	$(VENV) mypy cli_tool_audit --ignore-missing-imports --check-untyped-defs

check-llm: lint-llm test-llm
	@echo "LLM-friendly checks complete"


isort: 
	@echo "Formatting imports"
	$(VENV) isort .


black: isort 
	@echo "Formatting code"
	$(VENV) metametameta pep621
	$(VENV) black cli_tool_audit # --exclude .venv
	$(VENV) black tests # --exclude .venv
	$(VENV) git2md cli_tool_audit --ignore __init__.py __pycache__ --output SOURCE.md


pre-commit:  isort black
	@echo "Pre-commit checks"
	$(VENV) pre-commit run --all-files

bandit:  
	@echo "Security checks"
	$(VENV)  bandit cli_tool_audit -r --quiet



pylint:isort black 
	@echo "Linting with pylint"
	$(VENV) ruff check --fix cli_tool_audit
	$(VENV) pylint cli_tool_audit --fail-under 9.8


check: mypy test pylint bandit

publish: test
	rm -rf dist && $(VENV) hatch build

mypy:
	$(VENV) echo $$PYTHONPATH
	$(VENV) mypy cli_tool_audit --ignore-missing-imports --check-untyped-defs


check_docs:
	$(VENV) interrogate cli_tool_audit --verbose  --fail-under 70
	$(VENV) pydoctest --config .pydoctest.json | grep -v "__init__" | grep -v "__main__" | grep -v "Unable to parse"

make_docs:
	pdoc cli_tool_audit --html -o docs --force

docs-build:
	$(VENV) mkdocs build

docs-serve:
	$(VENV) mkdocs serve

docs-deploy:
	$(VENV) mkdocs gh-deploy

check_md:
	$(VENV) linkcheckMarkdown README.md
	$(VENV) markdownlint README.md --config .markdownlintrc
	$(VENV) mdformat README.md docs/*.md


check_spelling:
	$(VENV) pylint cli_tool_audit --enable C0402 --rcfile=.pylintrc_spell
	$(VENV) pylint docs --enable C0402 --rcfile=.pylintrc_spell
	$(VENV) codespell README.md --ignore-words=private_dictionary.txt
	$(VENV) codespell cli_tool_audit --ignore-words=private_dictionary.txt
	$(VENV) codespell docs --ignore-words=private_dictionary.txt

check_changelog:
	# pipx install keepachangelog-manager
	$(VENV) kaclm validate

check_all_docs: check_docs check_md check_spelling check_changelog

check_self:
	# Can it verify itself?
	$(VENV) ./scripts/dog_food.sh

pin_actions:
	pinact run --update .github/workflows/build.yml .github/workflows/publish_to_pypi.yml

# ── Dogfooding targets (independent, not wired into check) ───────────────────

.PHONY: version-check
version-check:
	@uv run jiggle_version check

.PHONY: dev-status
dev-status:
	@uv run troml-dev-status validate .

.PHONY: prerelease-check
prerelease-check: version-check dev-status
	@echo "Pre-release checks passed."

.PHONY: dont-be-lazy
dont-be-lazy:
	@uv run dont_be_lazy --root . --no-color summary
	@uv run dont_be_lazy --root . --no-color scan cli_tool_audit --no-config-suppressions || true

.PHONY: pydoc-docs
pydoc-docs:
	@uv run pydoc_fork cli_tool_audit -o ./pydoc/
