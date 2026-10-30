# Demo tập trung dự đoán lương

Ngày 30/10/2026, người dùng bỏ yêu cầu tư vấn nghề nghiệp khỏi phạm vi demo hiện tại, yêu cầu dự đoán lương là chức năng trọng tâm, giao diện trực quan, từ ngữ dễ hiểu và ít ghi chú. Sau khi hoàn tất, dọn cấu trúc/file không dùng, viết docs, commit và push lên nhánh mặc định thực tế `publish/salary-ml`.

Trang chính dùng Ridge đã lưu và đã được chọn bằng validation. Luồng mới là truy vấn theo nghề và thành phố, không phải hồ sơ cá nhân đầy đủ: không có ô kinh nghiệm/kỹ năng vì run hiện chưa học được các yếu tố đó. Các trường chưa quan sát dùng đúng biểu diễn missing của dữ liệu huấn luyện; không giả định 0 năm và không thêm feature mới vào vocabulary. Không thay nhãn, hyperparameter, split hoặc đánh giá test.

Giữ ngưỡng support đã khóa: ít nhất 3 tin/2 công ty cho nghề và ít nhất 3 tin khớp nghề/thành phố trong train. Hiện Data/ML tại HN/HCM đạt; nghề khác hoặc thành phố khác chưa đạt không trả lương. Đây là ước tính có điều kiện theo hai biến, không tuyên bố đã hỗ trợ dự đoán cá nhân theo kinh nghiệm/kỹ năng. Đơn vị và sai số thử nghiệm được ghi ngắn cạnh kết quả; metadata/kiểm toán để trong mục thu gọn và docs.

Bốn màn hình chính: dự đoán, thị trường, so sánh model, dữ liệu. Công cụ đối chiếu/preview vẫn cần cho kiểm dữ liệu và được gom ở pages/tools; không đưa toàn bộ vào menu chính. Các bước/ticket tư vấn cũ là lịch sử, không phải phần phải hoàn thành trong demo này. Demo vẫn chưa đáp ứng toàn bộ bài tập gốc nếu giảng viên yêu cầu tư vấn kỹ năng hoặc ảnh hưởng kinh nghiệm.
