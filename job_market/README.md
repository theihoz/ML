# Ứng dụng Streamlit

Bản demo dự đoán lương CNTT theo nghề và thành phố. Năm trang chính nằm trong pages/predict.py, overview.py, market.py, models.py và data.py. Các công cụ nhập/đối chiếu dữ liệu nằm riêng trong pages/tools.

Từ thư mục này, sau khi cài gói trong môi trường Python 3.11:

```sh
PYTHONPATH=src python -m streamlit run app.py --server.port 8502
make check PYTHON=python
PYTHONPATH=src python -m career_market predict --role Data/ML --location HN
PYTHONPATH=src python -m career_market training-report
```

Có thể chạy từ root bằng make demo/make check theo README gốc. Gói Python và dependency duy nhất của app được khai báo ở pyproject.toml trong thư mục này; không còn cấu hình TensorFlow/API web cũ.

Ridge tự huấn luyện từ 14 tin/11 công ty, chia theo công ty 10/2/2, đã lưu tại artifacts/runs/7137291a5d16b71f1861. Mở trang và bấm dự đoán chỉ nạp model, không fit lại. Demo cho phép chọn trực tiếp Ridge hoặc Linear Regression cho bảy nghề và ba thành phố, không chặn theo số mẫu. Nhóm chưa có trong train được encoder bỏ qua, không thêm feature hoặc fit lại. Không có tư vấn nghề nghiệp, không yêu cầu kinh nghiệm/kỹ năng chưa được model học đủ.

Dữ liệu thị trường và cohort dùng dự đoán được giữ riêng. Raw, nguồn/giấy phép, snapshot nhãn trước fit, policy và model đều được giữ để đối chiếu. Sai số test còn lớn (MAE 21,98 triệu/tháng trên 2 tin); demo chưa hoàn tất mọi yêu cầu của đề bài gốc. Chi tiết ở docs/DEMO.md và docs/rebuild/ml/TRAINING_RUN-2026-10-30.md tại root.
