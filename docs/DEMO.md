# Chạy thử dự đoán lương

Từ thư mục gốc repository, dùng Python 3.11:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install './job_market[dev]'
make demo
```

Mở http://127.0.0.1:8502. Dừng ứng dụng bằng Ctrl+C trong terminal.

## Thao tác

1. Mở trang Dự đoán lương.
2. Chọn Data/ML và Hà Nội hoặc TP. Hồ Chí Minh.
3. Bấm dự đoán để xem lương ước tính theo tháng và số mẫu hỗ trợ.

Mỗi cặp nghề–thành phố trên có 3 mẫu trong tập train. Trường hợp không đủ hỗ trợ sẽ không có số dự đoán. Demo không yêu cầu kinh nghiệm, kỹ năng hoặc đưa lời khuyên nghề nghiệp.

## Đọc kết quả

Ứng dụng nạp Ridge đã lưu, được chọn bằng validation; thao tác dự đoán không fit lại mô hình. Target là trung điểm khoảng lương chào tuyển có bằng chứng VND/tháng, chưa xác định gross/net.

Chỉ có 14 mẫu/11 công ty, chia 10 train, 2 validation và 2 test theo công ty. Test MAE 21,98 triệu đồng/tháng là sai số trung bình trên 2 mẫu test, không phải khoảng đảm bảo cho từng dự đoán. Mẫu ít và sai số lớn nên chỉ dùng để minh họa luồng dự đoán.

Không có số năm kinh nghiệm được xác minh trong cohort, kỹ năng chỉ có bằng chứng ở 3 tin. Vì vậy demo không cho nhập hai yếu tố này để điều chỉnh lương. Dữ liệu và kết quả hiện tại chưa chứng minh chất lượng trên thị trường chung hoặc hoàn thành toàn bộ yêu cầu đề bài.

Kiểm tra mã và kiểm thử từ thư mục gốc bằng `make check` sau khi kích hoạt môi trường.
