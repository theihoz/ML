# Ứng dụng Streamlit

Từ thư mục này, sau khi cài gói trong môi trường Python 3.11:

```sh
make run PYTHON=python                                   # mở web demo
make check PYTHON=python                                 # lint + kiểm thử
PYTHONPATH=src python -m career_market build-dataset     # tạo lại bộ salary-v2
PYTHONPATH=src python -m career_market train             # huấn luyện lại
PYTHONPATH=src python -m career_market validate          # kiểm định
PYTHONPATH=src python -m career_market advise --role "Backend Developer" --years 2 --skills "Java,SQL"
```

Bố cục mã: xem `docs/STRUCTURE.md` ở thư mục gốc.
