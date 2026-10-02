# Uses ./.venv if present, else /tmp/claude-0/venv-test (sandbox), else python3.
PY ?= $(firstword $(wildcard .venv/bin/python /tmp/claude-0/venv-test/bin/python) python3)

.PHONY: setup test lint typecheck eval check
setup:
	python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev]"
test:
	$(PY) -m pytest tests
lint:
	$(PY) -m ruff check packages apps employees tests evals
typecheck:
	$(PY) -m mypy packages apps employees
eval:
	$(PY) -m evals.run
check: lint test eval
