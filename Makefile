# Lệnh chạy từ thư mục gốc repository. Gõ `make help` để xem danh sách.
PYTHON ?= python3
PORT ?= 8502
VERSION ?= latest
CLI = cd job_market && PYTHONPATH=src $(PYTHON) -m career_market

.PHONY: help demo check test dataset train load valid scores versions rollback refresh

help:      ## Liệt kê các lệnh
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | expand -t 12

demo:      ## Mở web demo tại http://127.0.0.1:8502
	$(MAKE) -C job_market run PYTHON="$(PYTHON)" PORT="$(PORT)"

check:     ## Lint + toàn bộ kiểm thử
	$(MAKE) -C job_market check PYTHON="$(PYTHON)"

test:      ## Chỉ chạy kiểm thử (không lint)
	$(MAKE) -C job_market test PYTHON="$(PYTHON)"

dataset:   ## Bước 2: tạo lại bộ salary-v2 từ nguồn thô và các lô đã nhập
	$(CLI) build-dataset

train: dataset  ## Bước 3: huấn luyện thành phiên bản mới; chỉ phục vụ khi qua cổng (~30 giây)
	$(CLI) train

load:      ## Nạp model vừa train để phục vụ, kể cả khi trượt cổng (VERSION=tên để chọn bản khác)
	$(CLI) use $(VERSION)

valid:     ## Bước 5: kiểm định model đang phục vụ và đối chiếu báo cáo lương
	$(CLI) validate > /dev/null
	$(CLI) reality-check | $(PYTHON) -c "import json,sys; r=json.load(sys.stdin)['reference']; print('Đối chiếu báo cáo:', r['status'], f\"({r['pass_rate']:.0%} ô lệch ≤ 15%)\")"
	@$(MAKE) --no-print-directory scores PYTHON="$(PYTHON)"

scores:    ## In sai số MAE/RMSE/R²/MAPE của từng mô hình trên train / valid / test
	$(CLI) scores

versions:  ## Liệt kê các phiên bản model, đánh dấu bản đang phục vụ
	$(CLI) versions

rollback:  ## Quay lại phiên bản đã phục vụ trước đó
	$(CLI) rollback

refresh:   ## Nhập lô CSV (CSV="a.csv b.csv") rồi dựng, huấn luyện, qua cổng thay model
	$(CLI) refresh $(CSV)
