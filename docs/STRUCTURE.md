# Bố cục repository

Ứng dụng hiện tại nằm trong `job_market`. Chạy lệnh từ thư mục gốc theo README.

| Đường dẫn | Nội dung |
| --- | --- |
| `Makefile` | Lệnh chạy demo và kiểm tra từ thư mục gốc |
| `job_market/app.py` | Điều hướng năm trang chính |
| `job_market/pages/advisor.py` | Trang chủ: dự đoán lương và tư vấn kỹ năng theo hồ sơ |
| `job_market/pages/overview.py` | Dashboard tổng quan đủ 23 vai trò |
| `job_market/pages/evaluation.py`, `dataset.py` | Đánh giá mô hình salary-v2 và dữ liệu huấn luyện |
| `job_market/pages/market.py` | Nhu cầu kỹ năng theo nguồn |
| `job_market/pages/predict.py`, `models.py`, `data.py` | Bản thăm dò 14 nhãn, giữ làm hồ sơ (ẩn khỏi menu) |
| `job_market/src/career_market/salary_dataset.py` | Gộp ba nguồn, chuẩn hóa lương, vai trò, kỹ năng, chia train/valid/test |
| `job_market/src/career_market/salary_model.py` | Huấn luyện, đánh giá, giá trị kỹ năng và hàm tư vấn |
| `job_market/src/career_market/salary_charts.py`, `salary_app.py` | Biểu đồ Matplotlib/Seaborn và cache Streamlit |
| `job_market/artifacts/salary-v2/` | Mô hình, metric, dự đoán tập test và giá trị kỹ năng |
| `report/` | Báo cáo .docx, sơ đồ draw.io và hình minh họa |
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

Demo dùng vai trò, khu vực, kinh nghiệm và kỹ năng để gọi mô hình salary-v2 đã lưu; không huấn luyện lại khi dự đoán. Giữ dữ liệu, nhãn, policy và artifact cùng bằng chứng xuất xứ để đối chiếu kết quả.

Các ghi chép cũ có thể mô tả phạm vi trước đây, gồm tư vấn nghề nghiệp hoặc những phần chưa triển khai. Giữ chúng làm hồ sơ lịch sử; phạm vi demo hiện tại được mô tả trong README và `docs/DEMO.md`.
