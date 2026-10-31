# Dự đoán lương CNTT

Demo Streamlit dự đoán lương theo nhóm nghề và địa điểm, dùng hai mô hình Ridge và Linear Regression đã tự huấn luyện và lưu sẵn. Giao diện tiếng Việt, không tư vấn nghề nghiệp.

## Chạy demo

Dùng Python 3.11, chạy từ thư mục gốc repository:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install './job_market[dev]'
make demo
```

Mở http://127.0.0.1:8502. Kiểm tra mã và kiểm thử bằng `make check` trong cùng môi trường.

## Chạy bằng Docker

Yêu cầu Docker Engine và Docker Compose plugin:

```sh
docker compose up --build
```

Mở http://127.0.0.1:8502. Nhấn `Ctrl+C` để dừng; nếu chạy Compose ở chế độ nền bằng `docker compose up --build -d`, dùng `docker compose down` để dừng và xóa container.

## Phạm vi

Chọn Ridge hoặc Linear Regression, một trong bảy nhóm nghề và một trong ba thành phố HN/HCM/Đà Nẵng. Demo dùng trực tiếp pipeline đã lưu, không chặn chỉ vì ít mẫu và không thay bằng trung bình thành phố. Danh mục chưa có trong train được bộ mã hóa bỏ qua; một số nhóm vì thế có thể có kết quả giống nhau.

Không yêu cầu nhập kinh nghiệm hoặc kỹ năng: chưa có số năm kinh nghiệm được xác minh trong 14 mẫu; bằng chứng kỹ năng quá ít để hỗ trợ điều chỉnh dự đoán. Kết quả là lương chào tuyển ước tính theo VND/tháng, chưa xác định gross/net.

Run thăm dò có 14 mẫu từ 11 công ty, chia train/validation/test là 10/2/2 theo công ty. Ridge được chọn theo validation, giữ nguyên mô hình đã lưu, không huấn luyện khi bấm dự đoán. Test MAE là **21,98 triệu đồng/tháng**, sai số còn lớn và tập test chỉ có 2 mẫu. Đây là demo thăm dò, chưa phải bản mẫu đầy đủ theo đề bài hay công cụ xác định mức lương cá nhân.

Dashboard Tổng quan có bốn ô số liệu và biểu đồ công nghệ, kinh nghiệm–thu nhập, lương theo nghề, địa điểm. Các số liệu là dữ liệu đã tải của dự án, không phải dữ liệu trực tiếp hoặc tỷ lệ tăng trưởng.

Cách thao tác nằm trong `docs/DEMO.md`; bố cục mã trong `docs/STRUCTURE.md`. Số liệu gốc được ghi ở `docs/rebuild/ml/TRAINING_RUN-2026-10-30.md`.
