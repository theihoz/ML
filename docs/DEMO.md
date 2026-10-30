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
2. Chọn mô hình Ridge hoặc Linear Regression, nghề và thành phố.
3. Bấm dự đoán để xem mức lương và biểu đồ so sánh ba thành phố.
4. Mở Tổng quan để xem các ô thống kê và bốn biểu đồ theo bố cục dashboard.
5. Mở So sánh mô hình, đổi model và tập đánh giá để xem MAE/RMSE; nút Dự đoán với mô hình này đưa lựa chọn sang form.

Không áp dụng ngưỡng số mẫu để chặn demo. Lựa chọn chưa có trong train được pipeline mã hóa theo cách xử lý danh mục chưa biết đã có sẵn, không thêm vocabulary và không fit lại. Không yêu cầu kinh nghiệm/kỹ năng hoặc đưa lời khuyên nghề nghiệp.

## Đọc kết quả

Ứng dụng nạp đúng model bạn chọn. Ridge vẫn là lựa chọn mặc định từ validation; thao tác đổi model để so sánh không thay lựa chọn hoặc metric lịch sử và không fit lại mô hình. Target là trung điểm khoảng lương chào tuyển có bằng chứng VND/tháng, chưa xác định gross/net.

Chỉ có 14 mẫu/11 công ty, chia 10 train, 2 validation và 2 test theo công ty. Test MAE 21,98 triệu đồng/tháng là sai số trung bình trên 2 mẫu test, không phải khoảng đảm bảo cho từng dự đoán. Mẫu ít và sai số lớn nên chỉ dùng để minh họa luồng dự đoán.

Không có số năm kinh nghiệm được xác minh trong cohort, kỹ năng chỉ có bằng chứng ở 3 tin. Vì vậy demo không cho nhập hai yếu tố này để điều chỉnh lương. Dữ liệu và kết quả hiện tại chưa chứng minh chất lượng trên thị trường chung hoặc hoàn thành toàn bộ yêu cầu đề bài.

Kiểm tra mã và kiểm thử từ thư mục gốc bằng `make check` sau khi kích hoạt môi trường.

## Biểu đồ

Trang dự đoán vẽ ba đầu ra của model cho cùng nghề ở ba thành phố. Trang thị trường giữ riêng nhu cầu quan sát trong 320 tin, lương chào tuyển từ 14 tin năm 2026 và thu nhập tháng từ 2 tin YODY năm 2023. Không gộp các loại tiền/thu nhập để làm trung bình chung.

Biểu đồ kinh nghiệm chỉ dùng hai khoảng 1–5 và 2–5 năm có chứng cứ; không vẽ thêm điểm hoặc đường xu hướng giả. Biểu đồ lương theo kỹ năng mô tả trung điểm trong tin có nhắc kỹ năng, không chứng minh kỹ năng gây tăng thu nhập. Dashboard không sao chép số mẫu, USD/năm, tăng trưởng hoặc nhãn trực tiếp từ ảnh tham khảo.
