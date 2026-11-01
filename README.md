# Dự đoán lương CNTT và tư vấn kỹ năng

Ứng dụng Streamlit phân tích thị trường việc làm CNTT Việt Nam, dự đoán mức lương lập trình viên và gợi ý kỹ năng nên học thêm. Giao diện tiếng Việt.

## Chạy demo

Dùng Python 3.11, chạy từ thư mục gốc repository:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install './job_market[dev]'
make demo
```

Mở http://127.0.0.1:8502. Kiểm tra mã và kiểm thử bằng `make check` trong cùng môi trường. Tạo lại bộ dữ liệu và huấn luyện lại bằng `make train-v2` (khoảng 20 giây).

## Chạy bằng Docker

Yêu cầu Docker Engine và Docker Compose plugin:

```sh
docker compose up --build
```

Mở http://127.0.0.1:8502. Nhấn `Ctrl+C` để dừng; nếu chạy ở chế độ nền bằng `docker compose up --build -d`, dùng `docker compose down` để dừng.

## Dữ liệu và mô hình

Bộ dữ liệu `salary-v2` gộp ba nguồn thô sẵn có trong `job_market/datasets/raw` (TopCV 2026, Vietnam IT Job Posts 2026, CareerBuilder 2023). Từ 8.523 tin, 3.809 tin có lương đọc được, thuộc 23 vai trò CNTT và không trùng lặp. Lương chuẩn hóa về trung điểm khoảng, triệu VND/tháng. Mỗi tin có nhãn train/valid/test (2.461/652/696), chia 70/15/15 theo công ty để một công ty không nằm ở hai tập.

| Mô hình | MAE test | RMSE test | R² test | MAPE test |
| --- | --- | --- | --- | --- |
| Mốc trung vị | 12,15 | 17,17 | −0,04 | 48,3% |
| Ridge | 5,95 | 8,50 | 0,745 | 22,0% |
| Random Forest | 5,73 | 8,58 | 0,740 | 20,8% |
| **Gradient Boosting** (chọn theo valid) | **5,38** | **7,96** | **0,776** | **19,7%** |

Đơn vị MAE/RMSE: triệu VND/tháng. Kết quả là lương chào tuyển ước tính, chưa phân biệt gross/net.

## Các trang

- **Tư vấn & dự đoán lương** (trang chủ): nhập vai trò, khu vực, kinh nghiệm, kỹ năng; nhận lương dự đoán, khoảng thường gặp, kỹ năng nên học và lộ trình theo kinh nghiệm. Có thể chia sẻ hồ sơ qua đường dẫn, ví dụ `/?role=Data%20Engineer&years=3&skills=Python,SQL`.
- **Tổng quan**: dashboard top công nghệ theo nhu cầu và theo lương, kinh nghiệm – thu nhập, lương theo đủ 23 vai trò, theo khu vực và vai trò × khu vực.
- **Thị trường việc làm**: nhu cầu kỹ năng theo nguồn và bộ lọc.
- **Đánh giá mô hình**: MAE, RMSE, R², MAPE trên train/valid/test, thực tế – dự đoán, mức quan trọng đặc trưng, giá trị gia tăng của kỹ năng.
- **Dữ liệu huấn luyện**: phễu làm sạch, nhãn train/valid/test, tải CSV.

Bản thăm dò ban đầu (Ridge/Linear Regression trên 14 nhãn duyệt tay) vẫn giữ ở các đường dẫn ẩn `Du_doan_tham_do`, `Huan_luyen`, `Du_lieu` làm hồ sơ.

Báo cáo tiểu luận, sơ đồ draw.io và hình minh họa nằm trong `report/`. Cách thao tác nằm trong `docs/DEMO.md`; bố cục mã trong `docs/STRUCTURE.md`.
