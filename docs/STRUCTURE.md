# Bố cục repository

Ứng dụng hiện tại nằm trong `job_market`. Chạy lệnh từ thư mục gốc theo README.

| Đường dẫn | Nội dung |
| --- | --- |
| `Makefile` | Lệnh chạy demo và kiểm tra từ thư mục gốc |
| `job_market/app.py` | Điều hướng năm trang chính |
| `job_market/pages/overview.py` | Dashboard tổng quan bốn ô thống kê và bốn biểu đồ |
| `job_market/pages/predict.py` | Nhập lựa chọn và hiển thị lương dự đoán |
| `job_market/pages/market.py`, `models.py`, `data.py` | Biểu đồ, so sánh mô hình và bảng dữ liệu |
| `job_market/pages/tools/` | Công cụ kiểm nguồn, chuẩn hóa và nhập CSV/Excel |
| `job_market/src/career_market/` | Đọc dữ liệu, chuẩn hóa, phân tích, huấn luyện và dự đoán |
| `job_market/pyproject.toml` | Gói Python và các thư viện của ứng dụng |
| `job_market/tests/` | Kiểm thử ứng dụng và nghiệp vụ |
| `job_market/config/` | Chính sách nhãn và huấn luyện |
| `job_market/datasets/` | Dữ liệu thô, xuất xứ và nhãn đã rà soát |
| `job_market/artifacts/runs/` | Mô hình, chia tập, metric và bằng chứng của run đã lưu |
| `job_market/docs/tdd/` | Ghi chép kiểm thử từng phần |
| `docs/DEMO.md` | Hướng dẫn chạy và đọc kết quả |
| `docs/adr/`, `docs/rebuild/` | Lịch sử quyết định, nghiên cứu và báo cáo thực hiện |
| `.github/workflows/job-market.yml` | Kiểm tra tự động cho ứng dụng |

Demo dùng nghề và địa điểm để gọi Ridge hoặc Linear Regression theo lựa chọn trên web; không huấn luyện lại khi dự đoán. Giữ dữ liệu, nhãn, policy và artifact cùng bằng chứng xuất xứ để đối chiếu kết quả.

Các ghi chép cũ có thể mô tả phạm vi trước đây, gồm tư vấn nghề nghiệp hoặc những phần chưa triển khai. Giữ chúng làm hồ sơ lịch sử; phạm vi demo hiện tại được mô tả trong README và `docs/DEMO.md`.
