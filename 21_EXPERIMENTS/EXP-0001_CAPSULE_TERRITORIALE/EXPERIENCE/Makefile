PYTHON ?= python
PYTHONPATH := $(CURDIR)/src
export PYTHONPATH

.PHONY: demo test lint check

demo:
	$(PYTHON) -m gsie_execution_kit demo \
		--source fixtures/territoire-reference \
		--cases fixtures/golden-bench \
		--workdir build

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	$(PYTHON) -m ruff check src tests
	$(PYTHON) -m ruff format --check src tests
	$(PYTHON) -m mypy src --strict

check: lint
	$(PYTHON) -m compileall -q src tests
	$(PYTHON) -m unittest discover -s tests -v
