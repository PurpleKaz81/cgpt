PYTHON ?= python3
RUFF ?= $(if $(wildcard .venv/bin/python),.venv/bin/python -m ruff,$(PYTHON) -m ruff)

.PHONY: doctor test lint lint-py lint-md check tox setup-dev

doctor:
	$(PYTHON) cgpt.py doctor

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

lint-py:
	$(RUFF) check .

lint-md:
	npx --yes markdownlint-cli2@0.16.0 "**/*.md" "#node_modules" "#.venv" "#.tox"

lint: lint-py lint-md

check: test lint

tox:
	tox run -e py,lint

setup-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"
