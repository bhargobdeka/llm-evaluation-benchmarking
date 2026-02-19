PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: venv install lint typecheck test check precommit run-example run-groq report latest-run nightly

venv:
	python3 -m venv .venv
	$(PIP) install --upgrade pip

install:
	$(PIP) install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check src tests

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest -q

check: lint typecheck test

precommit:
	$(PYTHON) -m pre_commit run --all-files

run-example:
	$(PYTHON) -m llm_eval run --config configs/run.example.yaml --policy configs/policy.yaml --env .env

run-groq:
	$(PYTHON) -m llm_eval run --config configs/run.groq.yaml --policy configs/policy.yaml --env .env

latest-run:
	@ls -1 artifacts/runs | tail -n 1

report:
	$(PYTHON) -m llm_eval report --run-id "$$(ls -1 artifacts/runs | tail -n 1)" --artifacts-root artifacts --reports-root reports

nightly:
	$(PYTHON) scripts/run_nightly_eval.py --config configs/run.groq.yaml --policy configs/policy.yaml --env .env
