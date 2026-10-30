# So sánh model và dashboard cho demo học thuật

Ngày 30/10/2026, người dùng yêu cầu nới ngưỡng số mẫu, sau đó sửa rõ: để model dự đoán, không thay bằng trung bình thành phố và không thêm nhãn giải thích trên kết quả. Người dùng tiếp tục yêu cầu biểu đồ dự đoán, đổi model bằng tay trên web và dashboard tổng quan theo ảnh tham khảo.

Thay điều kiện inference của ADR0011: mọi cặp nghề/thành phố hợp lệ trong danh mục demo đi qua pipeline đã lưu, không chặn vì dưới số mẫu. Giữ kiểm tra đầu vào, checksum artifact, model allowlist, kết quả hữu hạn và dương. Không bịa kết quả trung bình dưới tên model. DictVectorizer đã fit train bỏ qua khóa danh mục chưa biết; đó không phải bằng chứng model đã học khác biệt cho mọi nghề/thành phố. Giới hạn này ghi trong docs, không thêm đoạn dài lên form.

Cho phép chọn Ridge hoặc Linear Regression trong form dự đoán và trang so sánh. Nạp đúng artifact được yêu cầu sau khi kiểm đầy đủ manifest; lựa chọn thủ công là thao tác demo, không thay quyết định chọn Ridge bằng validation hoặc metric/test/run đã khóa. Không fit lại hay dò tham số sau test.

Biểu đồ dự đoán là đầu ra của cùng model/nghề cho ba thành phố. Biểu đồ thị trường dùng trung điểm nhãn quan sát và số tin riêng theo nghề/khu vực/kỹ năng; giữ cohort lương chào tuyển năm 2026 tách khỏi thu nhập tháng YODY năm 2023. Không biến tương quan kỹ năng/lương thành quan hệ nhân quả.

Dashboard thêm các KPI và bốn biểu đồ theo bố cục ảnh. Dùng số liệu dự án: 320 tin EDA, 14 nhãn lương, hai model và hai tin thu nhập có khoảng kinh nghiệm. Không sao chép 52 nền tảng, 15.200 mẫu, USD/năm, tỷ lệ tăng trưởng hoặc trạng thái trực tiếp từ ảnh. Nhóm địa điểm trong biểu đồ tròn loại trừ lẫn nhau, cộng đúng tổng tin; Remote vẫn là hình thức làm việc riêng. Hai khoảng kinh nghiệm có thật được vẽ bằng điểm/khoảng, không thêm đường hồi quy giả.

Giao diện vẫn tập trung dự đoán lương; dashboard có đường dẫn riêng /Tong_quan và nút quay về form. Chưa khôi phục phần tư vấn kỹ năng mà người dùng đã bỏ khỏi phạm vi demo.
