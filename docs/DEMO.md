# Chạy thử dự đoán lương và tư vấn kỹ năng

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
