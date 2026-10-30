PYTHON ?= python3
PORT ?= 8502
export PYTHONPATH := src
export MPLCONFIGDIR := $(CURDIR)/.cache/matplotlib

.PHONY: check lint test run sources preview
check: lint test

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

test:
	$(PYTHON) -m pytest tests -q

run:
	$(PYTHON) -m streamlit run app.py --server.address 127.0.0.1 --server.port $(PORT)

sources:
	$(PYTHON) -m career_market sources

preview:
	$(PYTHON) -m career_market preview jobs-2023 --limit 5
