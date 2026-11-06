# Notebook giải thích ứng dụng

Mở notebook bằng kernel Python của môi trường `job_market` đã cài nhóm phụ thuộc `dev`, rồi chọn **Run All**. Các notebook dùng dữ liệu và mô hình lưu trong repo, không huấn luyện lại. File được commit không kèm output.

| Notebook | Nội dung |
| --- | --- |
| `gan_nhan_du_lieu.ipynb` | Quy tắc và kiểm tra chất lượng gán nhãn |
| `tinh_nang_1_du_lieu_huan_luyen.ipynb` | Dữ liệu thô, tin sinh tự động, chuẩn hóa lương và chia tập |
| `tinh_nang_2_tong_quan_thi_truong.ipynb` | Tổng quan 1.735 tin thật có lương |
| `tinh_nang_3_thi_truong_viec_lam.ipynb` | Trang Thị trường: pipeline strict riêng, 320 tin và 14 nhãn lương được chấp nhận; không dùng salary-v2 |
| `tinh_nang_4_danh_gia_mo_hinh.ipynb` | So sánh mô hình và giải thích dự đoán |
| `tinh_nang_5_kiem_dinh_va_chuan_production.ipynb` | Hiệu chỉnh khoảng, bootstrap, công bằng và chuẩn production |
| `tinh_nang_6_tu_van_du_doan_luong.ipynb` | Tư vấn cho hồ sơ đủ dữ liệu và ít dữ liệu |

Chạy kiểm tra từ thư mục `job_market`: `python -m pytest tests/test_feature_notebooks.py tests/test_labeling_notebook.py`.

Sinh lại sáu notebook từ thư mục gốc: `python report/scripts/make_notebooks.py job_market/notebooks`.
