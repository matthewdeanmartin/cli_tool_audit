# if you wrap everything in poetry run, it runs slower.
VENV := if env_var_or_default("VIRTUAL_ENV","") !="" { "" } else { "poetry run " }

PROJECT := "cli_tool_audit"

[doc("Install dependencies")]
lock:
	@echo "Installing dependencies"
	@poetry lock && poetry install --with dev --sync

[doc("Clean compiled")]
clean:
	{{VENV}} pyclean {{PROJECT}}

[doc("Run tests")]
test: clean
	@echo "Running unit tests"
	{{VENV}} pytest --doctest-modules cli_tool_audit
	# {{VENV}} python -m unittest discover
	{{VENV}} py.test tests -vv -n auto --cov=cli_tool_audit --cov-report=html --cov-fail-under 50
	{{VENV}} bash basic_test.sh

[doc("Format import statement with isort")]
isort:
	@echo "Formatting imports"
	{{VENV}} isort .

[doc("Format python with black")]
black: isort
	{{VENV}} metametameta poetry
	{{VENV}} black cli_tool_audit --exclude .venv
	{{VENV}} black tests --exclude .venv
	# {{VENV}} black scripts --exclude .venv

[doc("Run pre-commit checks")]
pre:
	{{VENV}} pre-commit run --all-files

[doc("Running pylint")]
pylint: isort black
	{{VENV}} ruff check . --fix
	{{VENV}} pylint cli_tool_audit --fail-under 9.8

[doc("Running bandit")]
bandit: pylint
	{{VENV}} bandit cli_tool_audit -r

[doc("Checks excluding documentation")]
check: mypy pylint bandit test pre

[doc("Build (zip) the python package")]
zip: test
	rm -rf dist && poetry build

[doc("Checks excluding documentation")]
mypy:
	{{VENV}} mypy cli_tool_audit --ignore-missing-imports --check-untyped-defs

docker:
	docker build -t cli_tool_audit -f Dockerfile .

[doc("Run interrogate and pydoctest")]
check_docs:
	{{VENV}} interrogate cli_tool_audit --verbose
	{{VENV}} pydoctest --config .pydoctest.json | grep -v "__init__" | grep -v "__main__" | grep -v "Unable to parse"

[doc("Generate docs with pdoc")]
make_docs:
	pdoc cli_tool_audit --html -o docs --force

check_md:
	{{VENV}} mdformat README.md docs/*.md
	# {{VENV}} linkcheckMarkdown README.md # it is attempting to validate ssl certs
	{{VENV}} markdownlint README.md --config .markdownlintrc

check_spelling:
	{{VENV}} pylint cli_tool_audit --enable C0402 --rcfile=.pylintrc_spell
	{{VENV}} codespell README.md --ignore-words=private_dictionary.txt
	{{VENV}} codespell cli_tool_audit --ignore-words=private_dictionary.txt

check_changelog:
	# pipx install keepachangelog-manager
	{{VENV}} changelogmanager validate

[doc("Check all documentation")]
check_all: check_docs check_md check_spelling check_changelog audit

check_own_ver:
	# Can it verify itself?
	{{VENV}} python dog_food_check.py

audit:
	# {{VENV}} python -m cli_tool_audit audit
	{{VENV}} tool_audit single cli_tool_audit --version=">=2.0.0"

check_dead:
    {{VENV}} vulture cli_tool_audit
    {{VENV}} deadcode cli_tool_audit