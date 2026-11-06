# Ứng dụng Streamlit

Từ thư mục này, sau khi cài gói trong môi trường Python 3.11:

```sh
make run PYTHON=python                                   # mở web demo
make check PYTHON=python                                 # lint + kiểm thử
PYTHONPATH=src python -m career_market build-dataset     # tạo lại bộ salary-v2
PYTHONPATH=src python -m career_market train             # huấn luyện thành phiên bản mới, qua cổng
PYTHONPATH=src python -m career_market validate          # kiểm định model đang phục vụ
PYTHONPATH=src python -m career_market reality-check     # đối chiếu với báo cáo lương
PYTHONPATH=src python -m career_market advise --role "Backend Developer" --years 2 --skills "Java,SQL"
```

## Thêm dữ liệu mới và huấn luyện lại

Lô tin tuyển dụng là file CSV có đúng các cột `source, title, company, location, salary_text, experience_text, description, url, posted_date`.

```sh
PYTHONPATH=src python -m career_market refresh lo_moi.csv --source "Tên nguồn"
```

`refresh` chạy một lượt: nhập lô (bản thô lưu bất biến trong `datasets/batches/`) → dựng bộ dữ liệu → huấn luyện thành một phiên bản mới trong `artifacts/` → kiểm định → cổng thay model. Mỗi bước in số tin mới, số tin vào hàng đợi duyệt tay, số tin trùng, và model được thay hay giữ kèm lý do. Bước nào lỗi thì dừng, model đang phục vụ giữ nguyên. Từ thư mục gốc có thể chạy `make refresh CSV="lo_moi.csv"` (đường dẫn tính từ `job_market/`).

Tin của lô mới mà bộ gắn nhãn không xử lý được (lương thoả thuận, lương bất thường, không phân loại được vai trò) được ghi vào `datasets/processed/review_queue.csv`. Duyệt bằng mục 11 của notebook `notebooks/gan_nhan_du_lieu.ipynb`; quyết định ghi vào `datasets/labels/reviewed.csv` và được áp dụng ở lần dựng sau.

## Phiên bản model

```sh
PYTHONPATH=src python -m career_market versions   # liệt kê phiên bản, đánh dấu bản đang phục vụ
PYTHONPATH=src python -m career_market rollback   # quay lại bản đã phục vụ trước đó
```

Con trỏ `artifacts/CURRENT` chỉ phiên bản đang phục vụ; không có file này thì dùng `artifacts/salary-v2` (phiên bản đầu tiên). Phiên bản trượt cổng vẫn được giữ để phân tích.

Bố cục mã: xem `docs/STRUCTURE.md` ở thư mục gốc.
