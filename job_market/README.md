# Ứng dụng Streamlit

Phân tích thị trường việc làm CNTT, dự đoán lương và tư vấn kỹ năng. Trang chính nằm trong pages/advisor.py, overview.py, market.py, evaluation.py và dataset.py; các công cụ đối chiếu dữ liệu nằm riêng trong pages/tools.

Từ thư mục này, sau khi cài gói trong môi trường Python 3.11:

```sh
PYTHONPATH=src python -m streamlit run app.py --server.port 8502
make check PYTHON=python
PYTHONPATH=src python -m career_market build-dataset
PYTHONPATH=src python -m career_market train-v2
PYTHONPATH=src python -m career_market advise --role "Backend Developer" --years 2 --skills "Java,SQL"
```

Bộ dữ liệu datasets/processed/salary_dataset_v2.csv có 3.809 tin, 23 vai trò, cột split train/valid/test chia theo công ty. Mô hình và metric lưu ở artifacts/salary-v2; Gradient Boosting đạt MAE test 5,38 triệu/tháng. Bản thăm dò 14 nhãn (artifacts/runs/7137291a5d16b71f1861) được giữ làm hồ sơ.
