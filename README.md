# Dự đoán lương CNTT

Demo Streamlit dự đoán lương theo nhóm nghề và địa điểm, dùng mô hình Ridge đã huấn luyện và lưu sẵn. Giao diện tiếng Việt, không tư vấn nghề nghiệp.

## Chạy demo

Dùng Python 3.11, chạy từ thư mục gốc repository:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install './job_market[dev]'
make demo
```

Mở http://127.0.0.1:8502. Kiểm tra mã và kiểm thử bằng `make check` trong cùng môi trường.

## Phạm vi

Chọn nghề Data/ML và địa điểm Hà Nội hoặc TP. Hồ Chí Minh. Mỗi cặp nghề–thành phố có 3 mẫu train hỗ trợ. Những lựa chọn chưa đủ dữ liệu không trả số dự đoán.

Không yêu cầu nhập kinh nghiệm hoặc kỹ năng: chưa có số năm kinh nghiệm được xác minh trong 14 mẫu; bằng chứng kỹ năng quá ít để hỗ trợ điều chỉnh dự đoán. Kết quả là lương chào tuyển ước tính theo VND/tháng, chưa xác định gross/net.

Run thăm dò có 14 mẫu từ 11 công ty, chia train/validation/test là 10/2/2 theo công ty. Ridge được chọn theo validation, giữ nguyên mô hình đã lưu, không huấn luyện khi bấm dự đoán. Test MAE là **21,98 triệu đồng/tháng**, sai số còn lớn và tập test chỉ có 2 mẫu. Đây là demo thăm dò, chưa phải bản mẫu đầy đủ theo đề bài hay công cụ xác định mức lương cá nhân.

Cách thao tác nằm trong `docs/DEMO.md`; bố cục mã trong `docs/STRUCTURE.md`. Số liệu gốc được ghi ở `docs/rebuild/ml/TRAINING_RUN-2026-10-30.md`.
