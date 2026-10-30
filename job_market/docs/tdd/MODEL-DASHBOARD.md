# Model thủ công và dashboard tổng quan

Phạm vi mới theo ADR0012: cho chạy trực tiếp hai pipeline đã lưu cho mọi lựa chọn nghề/thành phố hợp lệ trong demo; không chặn theo số mẫu, không thay bằng trung bình thành phố, không fit lại. Input sai, artifact lỗi hoặc đầu ra vô hạn/âm vẫn bị từ chối.

TDD qua MarketService: test thiếu ngưỡng được đổi từ unsupported sang dự đoán thật; test mới kiểm 42 tổ hợp bảy nghề × ba thành phố × hai model. Red trước green cho model_name, salary_scenarios, salary_analysis và market_overview. Model-name allowlist và toàn bộ checksum artifact vẫn được kiểm trước nạp pipeline.

Kiểm biểu đồ bằng phép tính độc lập: Backend có 21 và 19,5 triệu nên trung bình các trung điểm là 20,25 triệu; tổng vùng trong donut bằng đúng 320 tin; 14 trung điểm lương có trung bình khoảng 45,107 triệu; kinh nghiệm giữ đúng khoảng (1,5) và (2,5) từ hai tin thu nhập, không thêm điểm/đường hồi quy. PNG sinh bằng Matplotlib/Seaborn, không dùng hình minh họa thay dữ liệu.

AppTest kiểm đổi model đổi kết quả/MAE/RMSE, nút dùng model đưa đúng lựa chọn sang form, ảnh dự đoán có ba thành phố, dashboard có bốn ảnh/KPI đúng và shortcut về dự đoán. Browser thực kiểm OLS tại Hà Nội cho Data/ML khoảng 28,3 triệu, so Ridge khoảng 34,5 triệu; đổi model trang so sánh cho MAE 17,58/RMSE 17,66 đúng OLS. Overview hiển thị 320 tin, 14 nhãn, hai model, bốn biểu đồ, không exception.

Review Spec/Standards phát hiện và đã sửa nhãn thu nhập/lương, lookup Image trong AppTest, ảnh None, xử lý lỗi biểu đồ, cache theo hash bằng chứng và sinh đúng loại biểu đồ cần xem. Lỗi MAE dùng nhầm Ridge khi chọn OLS cũng đã sửa và có regression literal. Recheck không còn finding cần sửa trong phạm vi này.

Kiểm tra toàn bộ: 323 passed trong 107,81 giây; lint/format đạt. Sau sửa metadata/error-cache, tám test service/CLI/UI liên quan đạt. Không đổi report/model/metric đã đánh giá. Các giới hạn dữ liệu giữ trong README/docs; màn dự đoán không thêm đoạn giải thích dài. Bố cục overview tham chiếu ảnh người dùng nhưng không sao chép các con số thị trường, USD/năm, tăng trưởng hay nhãn trực tiếp trong ảnh.
