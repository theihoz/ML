# Bố cục repository

Luồng xử lý đi theo 5 bước, mỗi bước một file trong `job_market/src/career_market/`:

| Bước | File | Làm gì |
| --- | --- | --- |
| 1 | `data/rules.py` | Chuẩn hóa một tin: vai trò, lương triệu VND/tháng, kinh nghiệm, cấp bậc, khu vực, kỹ năng |
| 2 | `data/dataset.py` | Đọc 3 nguồn thô, lọc, khử trùng lặp, chia train/valid/test theo công ty |
| 3a | `model/estimators.py` | Ma trận đặc trưng và 4 mô hình (mốc trung vị, Ridge, Random Forest, Gradient Boosting) |
| 3b | `model/training.py` | Dò siêu tham số trên valid, chọn mô hình, lưu artifact |
| 4 | `model/advisor.py` | Dự đoán cho hồ sơ, gợi ý kỹ năng, lộ trình kinh nghiệm |
| 5 | `model/validation.py` | Hiệu chuẩn khoảng, bootstrap theo công ty, công bằng theo nhóm |

Phần còn lại:

| Đường dẫn | Nội dung |
| --- | --- |
| `job_market/app.py`, `pages/` | Giao diện Streamlit: 5 trang |
| `src/career_market/ui/` | Biểu đồ (`charts.py`), bộ nhớ đệm (`cache.py`), CSS (`theme.py`) |
| `src/career_market/paths.py` | Đường dẫn dữ liệu và mô hình |
| `src/career_market/__main__.py` | Dòng lệnh `build-dataset`, `train`, `validate`, `advise` |
| `job_market/datasets/` | Dữ liệu thô và bộ salary-v2 |
| `job_market/artifacts/salary-v2/` | Mô hình, metric, dự đoán test, giá trị kỹ năng, kiểm định |
| `job_market/tests/test_salary.py` | Kiểm thử từ chuẩn hóa đến giao diện |
| `docker/`, `Dockerfile`, `docker-compose.yaml` | Đóng gói demo chạy không cần mạng |
| `docs/adr/` | Các quyết định thiết kế đã qua |
| `report/` | Báo cáo .docx, slide, sơ đồ draw.io, hình |
