# Lệnh chạy từ thư mục gốc repository.
PYTHON ?= python3
PORT ?= 8502
CLI = cd job_market && PYTHONPATH=src $(PYTHON) -m career_market

.PHONY: demo check dataset train
demo:      ## Mở web demo tại http://127.0.0.1:8502
	$(MAKE) -C job_market run PYTHON="$(PYTHON)" PORT="$(PORT)"

check:     ## Lint + kiểm thử
	$(MAKE) -C job_market check PYTHON="$(PYTHON)"

dataset:   ## Bước 2: tạo lại bộ salary-v2 từ 3 nguồn thô
	$(CLI) build-dataset

train: dataset  ## Bước 3 + 5: huấn luyện lại và kiểm định (~20 giây)
	$(CLI) train
	$(CLI) validate > /dev/null
