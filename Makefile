PYTHON ?= python3
PORT ?= 8502

.PHONY: demo check train
demo:
	$(MAKE) -C job_market run PYTHON="$(PYTHON)" PORT="$(PORT)"

check:
	$(MAKE) -C job_market check PYTHON="$(PYTHON)"

train:
	cd job_market && PYTHONPATH=src $(PYTHON) -m career_market train
