# Chạy thử dự đoán lương và tư vấn kỹ năng

## Demo bằng Docker Compose

Khởi động Docker Desktop trước. Chạy tại thư mục gốc repository, nơi có `docker-compose.yaml`.

Chuẩn bị khi có mạng (tải base image và thư viện, đóng gói dữ liệu/model sẵn có):

```sh
docker compose up --build -d --wait
docker compose exec app python /opt/demo/check_demo.py
```

Mở http://localhost:8502, thử bấm **Dự đoán & tư vấn**, đổi mô hình, rồi mở các trang Tổng quan, Thị trường, Đánh giá mô hình và Dữ liệu huấn luyện. Sau khi thử xong:

```sh
docker compose stop
```

Ngày demo, chỉ cần bật Docker rồi chạy:

```sh
docker compose up -d --wait --no-build --pull never
```

Lệnh này dùng image `ml-salary-demo:local` đã chuẩn bị, không cần Internet, Python trên máy hay huấn luyện lại. Cũng có thể bấm Start nhóm Compose đã có trong Docker Desktop. Nếu máy báo thiếu image, hãy build trước khi đến buổi demo. Khi khởi động, kiểm tra dữ liệu và dự đoán thật phải thành công trước khi Streamlit được mở; `--wait` đợi HTTP healthcheck sẵn sàng. Nếu lệnh thất bại, đọc `docker compose logs --tail=100 app`.

Ứng dụng chạy hoàn toàn trong một service `app`; model được nạp trực tiếp trong Python, không cần service model, database hay API key riêng. Không gắn thư mục máy chủ vào container, nên image giữ nguyên dữ liệu/model đã kiểm tra. Khi thay mã hoặc model, chạy lại lệnh build lúc chuẩn bị.

Mang image sang **máy cùng kiến trúc CPU** (ví dụ ARM64 → ARM64, AMD64 → AMD64):

```sh
# Máy chuẩn bị
docker image save -o ml-salary-demo.tar ml-salary-demo:local

# Máy demo: chép repository và file tar sang, mở Docker, rồi chạy từ repository
docker image load -i ml-salary-demo.tar
docker compose up -d --wait --no-build --pull never
```

Nếu đổi giữa Mac Apple Silicon và máy Windows/Linux AMD64, hãy build trực tiếp trên máy demo khi còn mạng. Không xóa image hoặc chạy Docker prune trước buổi demo. Có thể dừng bằng `docker compose stop`; để xóa container dùng `docker compose down`.

## Chạy bằng Python

Từ thư mục gốc repository, dùng Python 3.11:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install './job_market[dev]'
make demo
```

Mở http://127.0.0.1:8502. Dừng ứng dụng bằng Ctrl+C trong terminal.

## Thao tác

1. Trang chủ **Tư vấn & dự đoán lương**: chọn vai trò, khu vực, số năm kinh nghiệm, các kỹ năng đang có và mô hình, rồi bấm **Dự đoán & tư vấn**.
2. Đọc mức lương ước tính, khoảng thường gặp (80% tin tương tự) và vị trí so với trung vị thị trường của vai trò.
3. Xem bảng **Kỹ năng nên học thêm**: mức tăng lương dự đoán khi bổ sung từng kỹ năng và tỉ lệ tin của vai trò yêu cầu kỹ năng đó.
4. Xem **Lộ trình theo kinh nghiệm**: lương dự đoán khi tăng thêm 1, 2, 3, 5 năm.
5. Mở **Tổng quan** để xem dashboard đủ 23 vai trò, **Đánh giá mô hình** để so sánh metric, **Dữ liệu huấn luyện** để xem nhãn train/valid/test.

Tư vấn từ dòng lệnh:

```sh
cd job_market
PYTHONPATH=src python -m career_market advise --role "Data Engineer" --years 3 --skills "Python,SQL"
```

## Đọc kết quả

Ứng dụng chỉ nạp mô hình đã lưu trong `job_market/artifacts/salary-v2`, không huấn luyện lại khi bấm dự đoán. Gradient Boosting được chọn theo MAE trên tập valid; MAE trên tập test là 5,38 triệu/tháng trên 696 tin.

Mức tăng lương theo kỹ năng là quan hệ học được từ tin tuyển dụng, không phải quan hệ nhân quả. Dữ liệu lệch về Hà Nội (87% số tin có lương), nên kết quả cho TP. Hồ Chí Minh và Đà Nẵng kém chắc chắn hơn.

## Huấn luyện lại

```sh
make train-v2
```

Lệnh tạo lại `job_market/datasets/processed/salary_dataset_v2.csv` (có cột `split`) rồi huấn luyện Ridge, Random Forest, Gradient Boosting và mốc trung vị, ghi metric vào `metrics.json`.
