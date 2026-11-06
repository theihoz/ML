# Lương dự đoán đơn điệu theo kỹ năng

Ngày 06/11/2026, người dùng báo lỗi trên trang tư vấn salary-v2. Khi giữ nguyên vai trò nghề nghiệp, khu vực và kinh nghiệm, một kỹ năng như Java cho lương thấp hơn hồ sơ không có kỹ năng nào. Thêm từ hai kỹ năng trở lên đôi khi còn làm lương giảm. Ví dụ, Backend Developer ở Hà Nội với 5 năm kinh nghiệm: không kỹ năng 47.7tr, Java 42.3tr. Người dùng chọn quy tắc cứng: thêm kỹ năng không bao giờ làm lương dự đoán giảm.

Nguyên nhân nằm ở bản chất dữ liệu. Cột kỹ năng ghi những gì tin tuyển dụng yêu cầu, không phải những gì ứng viên có. Tin liệt kê nhiều kỹ năng thường là tin junior hoặc tin tuyển hàng loạt: với Backend, tin có 7–8 kỹ năng có trung vị khoảng 21.5tr, tin có 2 kỹ năng khoảng 29.5tr. Đặc trưng đếm số kỹ năng (`skill_count`) và các cột kỹ năng không có ràng buộc dấu đã học tương quan đó. Đây là tín hiệu thật để dự đoán lương chào tuyển, nhưng nó trả lời sai câu hỏi của trang tư vấn: biết thêm một kỹ năng thì lương thay đổi thế nào.

Quyết định:

- Bỏ đặc trưng `skill_count`.
- Gradient Boosting có ràng buộc đơn điệu +1 cho mọi cột kỹ năng, và giữ ràng buộc +1 cho kinh nghiệm. Đây là mô hình được chọn theo valid MAE và phục vụ dự đoán lẫn tư vấn.
- Ridge và Random Forest cũng được ràng buộc, để người dùng chọn mô hình thủ công không gặp lại lỗi. Ridge chặn hệ số kỹ năng ≥ 0 bằng bình phương tối thiểu có chặn. Random Forest được bọc bao đơn điệu: dự đoán cho một bộ kỹ năng là max của mô hình gốc trên mọi tập con của bộ đó. Với 12 kỹ năng (mức tối đa của một tin trong dữ liệu), một lần dự đoán mất khoảng 0.1s.
- Mức tăng của từng kỹ năng vẫn do dữ liệu quyết định. Không ép mức cộng tối thiểu, nên có kỹ năng cộng gần 0 (ví dụ Java). Hồ sơ không kỹ năng trở thành mức sàn và thấp hơn trước: ở 5 năm, từ 47.7tr xuống 39.8tr.

Ngân sách độ chính xác ban đầu là MAE test tăng tối đa 5% (≤ 5.65tr so với 5.38tr). Sau khi train lại, MAE test là 5.82tr (+8.2%). Đã thử chọn theo valid với nhiều learning rate, số lá, l2, min leaf, số vòng, loss MAE, tách interaction giữa kỹ năng và các đặc trưng khác, và bao đơn điệu trên mô hình không ràng buộc. Valid MAE luôn nằm trong khoảng 5.68–7.3, so với 5.35 khi không ràng buộc. Như vậy phần mất mát đến từ chính ràng buộc, không phải từ siêu tham số. Người dùng duyệt nới ngân sách lên 5.85tr. Không chỉnh siêu tham số theo test.

Ghi chú về ADR 0009: ADR 0009 nói chỉ giữ kỹ năng có delta > 0 và tối đa ba gợi ý. Tư vấn salary-v2 hiện trả tối đa năm gợi ý và bổ sung kỹ năng được yêu cầu nhiều khi không đủ kỹ năng có delta dương. Lệch này có từ trước quyết định này. Ràng buộc đơn điệu làm nhiều kỹ năng có delta gần 0, nên nhánh bổ sung xuất hiện thường hơn. ADR này không sửa ADR 0009. Việc thống nhất hai bên cần quyết định riêng.

Mức tăng trong tư vấn vẫn là chênh lệch dự đoán của mô hình, không phải bằng chứng nhân quả rằng học kỹ năng sẽ tăng thu nhập. Các test hành vi (thêm kỹ năng không làm giảm lương, gợi ý có mức tăng ≥ 0, ngân sách MAE ≤ 5.85) chạy trên artifact đã lưu, để chặn lỗi tái phát khi train lại.
