# Demo dự đoán lương

Phạm vi mới theo ADR0011: dự đoán theo nghề và thành phố, không có tư vấn nghề nghiệp hoặc ô kinh nghiệm/kỹ năng chưa được model hỗ trợ. Bốn trang chính nằm ở pages; công cụ đối chiếu còn dùng nằm ở pages/tools.

MarketService.estimate_salary nạp đúng Ridge đã chọn bằng validation, kiểm artifact và ngưỡng support trước trả kết quả. Truy vấn dùng biểu diễn missing của snapshot đã khóa, không fit, sửa model hoặc dùng test để chọn lại. Data/ML tại HN trả khoảng 34,5 triệu/tháng và HCM khoảng 63,2 triệu; đây là đầu ra model trên cohort nhỏ, không phải lương thị trường đã xác thực.

TDD: test service mới ban đầu lỗi thiếu estimate_salary; sau triển khai nhận lương thật từ artifact, unsupported không có số. CLI tiến trình mới trả cùng kết quả. AppTest kiểm trang chính, hai thành phố cho kết quả khác nhau, không JSON kỹ thuật trên màn chính, không ô kinh nghiệm/skill, thiếu support không trả lương. Regression sau review giữ đúng HCM và kết quả sau khi chuyển trang; bảng dữ liệu ghi rõ trung điểm và vai trò 10/2/2 của mẫu, lấy bằng chứng đã kiểm hash qua service.

Hai review độc lập Spec/Standards đã phát hiện và sửa trạng thái form sau điều hướng, nhãn bảng gây hiểu nhầm, link nguồn sai và đọc evidence trực tiếp ở adapter. Đã recheck các sửa này. Browser desktop xác nhận bấm dự đoán hiện 34,5 triệu, không exception; layout hẹp 500px xếp hai khối thành một cột và không tràn ngang. Cấu hình theme sáng và màu chữ được kiểm bằng ảnh/DOM. Không kiểm thiết bị điện thoại thật.

Giới hạn dữ liệu và sai số được ghi ngắn cạnh kết quả, phần chi tiết nằm trong expander/docs. Không thay model/metric lịch sử hoặc huấn luyện lại. Tài liệu demo ở docs/DEMO.md, cấu trúc ở docs/STRUCTURE.md tại root. Kiểm tra cuối bằng make check từ root: 316 test đạt trong 91,75 giây; Ruff lint và format đạt. Nhánh mặc định GitHub đã xác minh là publish/salary-ml; lịch sử hiện có được merge trước khi publish, không force push.
