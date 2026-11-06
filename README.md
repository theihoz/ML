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

Mở http://127.0.0.1:8502. Kiểm tra mã và kiểm thử bằng `make check` trong cùng môi trường. Tạo lại bộ dữ liệu và huấn luyện lại bằng `make train` (khoảng 30 giây). Model mới được ghi vào `artifacts/salary-v2-candidate` và chỉ thay model đang phục vụ khi qua cổng chuẩn production (đạt chuẩn, hoặc tốt hơn model hiện tại khi cả hai chưa đạt); lệnh in rõ thay hay giữ và lý do.

## Chạy bằng Docker

Yêu cầu Docker Desktop đang chạy (Windows/macOS), hoặc Docker Engine và Docker Compose plugin (Linux). Không cần cài Python riêng.

Từ thư mục gốc repository, chuẩn bị và chạy thử **trước ngày demo**, khi có Internet:

```sh
docker compose up --build -d --wait
```

Mở http://localhost:8502. Image chứa mã ứng dụng, ba nguồn dữ liệu, bộ salary-v2, toàn bộ model đã huấn luyện và metric. Khi build và khởi động, hệ thống kiểm tra dự đoán thật với cả 4 model và tư vấn kỹ năng. Không cần tải dữ liệu hay huấn luyện lại khi demo.

**Ngày demo**, trên máy đã build thành công và còn giữ image, bật Docker rồi chạy đúng một lệnh (dùng được khi không có mạng):

```sh
docker compose up -d --wait --no-build --pull never
```

Hoặc trong Docker Desktop → Containers, bấm Start cho nhóm Compose của dự án nếu nhóm đã được tạo trước đó. Đợi container báo healthy rồi mở http://localhost:8502.

- Kiểm tra trạng thái: `docker compose ps`.
- Xem lỗi khởi động: `docker compose logs --tail=100 app`.
- Kiểm tra lại model: `docker compose exec app python /opt/demo/check_demo.py`.
- Dừng và giữ container để lần sau bấm Start: `docker compose stop`.
- Xóa container, giữ image: `docker compose down`.

Nếu cổng 8502 đang bận, chạy `DEMO_PORT=8503 docker compose up -d --wait --no-build --pull never` rồi mở http://localhost:8503 (PowerShell: đặt `$env:DEMO_PORT=8503` trước khi chạy Compose).

Để mang sang máy khác cùng kiến trúc CPU mà không build qua mạng, xem [hướng dẫn demo](docs/DEMO.md#demo-bằng-docker-compose).

## Dữ liệu và mô hình

Bộ dữ liệu `salary-v2` gộp ba nguồn thô sẵn có trong `job_market/datasets/raw` (TopCV 2026, Vietnam IT Job Posts 2026, CareerBuilder 2023). Từ 8.523 tin, 3.809 tin có lương đọc được, thuộc 23 vai trò CNTT và không trùng lặp. Lương chuẩn hóa về trung điểm khoảng, triệu VND/tháng. Mỗi tin có nhãn train/valid/test (2.461/652/696), chia 70/15/15 theo công ty để một công ty không nằm ở hai tập.

| Mô hình | MAE test | RMSE test | R² test | MAPE test |
| --- | --- | --- | --- | --- |
| Mốc trung vị | 12,15 | 17,17 | −0,04 | 48,3% |
| Ridge | 6,37 | 9,03 | 0,712 | 23,4% |
| Random Forest | 6,47 | 9,14 | 0,705 | 25,5% |
| **Gradient Boosting** (chọn theo valid) | **5,82** | **8,58** | **0,740** | **20,7%** |

Đơn vị MAE/RMSE: triệu VND/tháng. Mọi mô hình bị ràng buộc "thêm kỹ năng không làm giảm lương" (ADR 0013). Kết quả là lương chào tuyển ước tính, chưa phân biệt gross/net.

## Các trang

- **Tư vấn & dự đoán lương** (trang chủ): nhập vai trò, khu vực, kinh nghiệm, kỹ năng; nhận lương dự đoán, khoảng thường gặp, kỹ năng nên học và lộ trình theo kinh nghiệm. Có thể chia sẻ hồ sơ qua đường dẫn, ví dụ `/?role=Data%20Engineer&years=3&skills=Python,SQL`.
- **Tổng quan**: dashboard top công nghệ theo nhu cầu và theo lương, kinh nghiệm – thu nhập, lương theo đủ 23 vai trò, theo khu vực và vai trò × khu vực.
- **Thị trường việc làm**: kỹ năng được yêu cầu nhiều và lương cao, lọc theo nguồn, vai trò, khu vực.
- **Đánh giá mô hình**: MAE, RMSE, R², MAPE trên train/valid/test, thực tế – dự đoán, mức quan trọng đặc trưng, giá trị gia tăng của kỹ năng.
- **Dữ liệu huấn luyện**: phễu làm sạch, nhãn train/valid/test, tải CSV.

## Cấu trúc thư mục

```
job_market/
├── app.py                  Điểm vào Streamlit, menu 5 trang
├── pages/                  5 trang giao diện
│   ├── advisor.py          Tư vấn & dự đoán lương (trang chủ)
│   ├── overview.py         Tổng quan
│   ├── market.py           Thị trường việc làm
│   ├── evaluation.py       Đánh giá mô hình
│   └── dataset.py          Dữ liệu huấn luyện
├── src/career_market/      Lõi xử lý (đọc theo thứ tự bước)
│   ├── data/rules.py       Bước 1: chuẩn hóa một tin
│   ├── data/dataset.py     Bước 2: gộp 3 nguồn, chia train/valid/test
│   ├── model/estimators.py Bước 3a: đặc trưng + 4 mô hình
│   ├── model/training.py   Bước 3b: huấn luyện, chọn mô hình
│   ├── model/advisor.py    Bước 4: dự đoán + gợi ý kỹ năng
│   ├── model/validation.py Bước 5: kiểm định
│   ├── ui/                 Biểu đồ, cache, theme
│   ├── paths.py            Đường dẫn dữ liệu/mô hình
│   └── __main__.py         Dòng lệnh
├── datasets/raw/           3 file CSV gốc
├── datasets/processed/     Bộ salary-v2 đã làm sạch
├── artifacts/salary-v2/    Mô hình .joblib và metric đã lưu
└── tests/test_salary.py    Kiểm thử toàn luồng
docker/                     Kiểm tra khi khởi động container
docs/                       Hướng dẫn demo, quyết định thiết kế (adr/)
report/                     Báo cáo, slide, sơ đồ, hình
```

Cách thao tác nằm trong `docs/DEMO.md`.
