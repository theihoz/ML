# Thị trường việc làm CNTT và lương lập trình viên

Các thuật ngữ của dự án làm mới trên branch `dev/job-market-ml-from-scratch`.

## Ngôn ngữ chung

**Tin tuyển dụng**:
Thông tin do bên tuyển dụng công bố về một vị trí, có thể gồm yêu cầu công việc, kỹ năng, kinh nghiệm, địa điểm và lương chào tuyển.
_Tránh dùng_: Bản ghi khảo sát lập trình viên.

**Lương chào tuyển**:
Mức hoặc khoảng lương được công bố trong tin tuyển dụng, gắn với tiền tệ và kỳ trả lương; không đồng nghĩa với thu nhập thực nhận của một lập trình viên.
_Tránh dùng_: Thu nhập khảo sát, lương thực nhận khi nguồn chưa xác nhận.

**Nhãn địa điểm chuẩn**:
Tên thống nhất cho các cách viết cùng một địa điểm; ví dụ `HCM`, `Hồ Chí Minh` và `ho chi minh` cùng có nhãn `HCM`.
_Tránh dùng_: Nhãn lương, mã số địa điểm không có giải thích.

**Nhãn lương**:
Giá trị lương có nguồn chứng minh, dùng làm mục tiêu của bài toán dự đoán và luôn gắn với tiền tệ cùng kỳ trả lương.
_Tránh dùng_: Nhãn địa điểm, mức lương tự điền khi nguồn thiếu thông tin.

**Lương trung điểm**:
Trung bình cộng của hai đầu một khoảng lương chào tuyển đã xác định tiền tệ và kỳ trả lương; ví dụ 20–30 triệu VND/tháng có trung điểm 25 triệu VND/tháng.
_Tránh dùng_: Lương trung vị của thị trường, lương thực nhận.

**Thu nhập tháng chào tuyển**:
Khoảng thu nhập một tháng được tin công bố và có chứng cứ tiền tệ/kỳ; giữ thành nhóm riêng theo ADR 0007. Không tự xác nhận cấu phần lương cơ bản hoặc cộng thưởng năm vào trung điểm tháng.
_Tránh dùng_: Lương cơ bản đã xác nhận, thu nhập thực nhận.

**Basis gross/net**:
Cách tin nguồn xác định gross hoặc net; ghi unknown khi nguồn không nói rõ. Nhóm unknown giữ riêng theo ADR 0006, độc lập với việc khoản tiền là lương cơ bản hay thu nhập tháng chào tuyển.
_Tránh dùng_: Tự coi unknown là gross, loại thu nhập.

**Vai trò nghề nghiệp**:
Nhóm công việc dùng để so sánh lương và tư vấn, gồm Backend, Frontend, Fullstack, Mobile, Data/ML, DevOps và QA Automation.
_Tránh dùng_: Cấp bậc, kỹ năng đơn lẻ.

**Địa điểm làm việc**:
Một hoặc nhiều địa điểm vật lý mà tin tuyển dụng cho phép làm việc; một tin có cả HCM và HN vẫn là một tin tuyển dụng.
_Tránh dùng_: Hình thức làm việc.

**Hình thức làm việc**:
Cách tổ chức công việc, trong đó Remote biểu thị làm việc từ xa và được ghi nhận độc lập với địa điểm vật lý.
_Tránh dùng_: Tỉnh hoặc thành phố.

**Nhu cầu tuyển dụng quan sát được**:
Sự xuất hiện của vai trò hoặc kỹ năng trong tập tin tuyển dụng được phân tích, giới hạn trong phạm vi nguồn và thời gian của tập đó.
_Tránh dùng_: Tỷ lệ người dùng công nghệ trong khảo sát, tổng nhu cầu của toàn thị trường.

**Xu hướng theo thời gian**:
Sự thay đổi của một chỉ tiêu giữa các giai đoạn có thời gian nguồn xác định và phạm vi dữ liệu đủ so sánh.
_Tránh dùng_: Bảng xếp hạng tại một thời điểm, năm tải dữ liệu thay cho năm đăng tin.

**Khoảng lương dự đoán**:
Khoảng từ phân vị 10 đến phân vị 90 mà hệ thống kỳ vọng lương chào tuyển của một hồ sơ rơi vào khoảng 80% số lần; là thông tin chính hiển thị cho người dùng, kèm hoặc thay cho con số dự đoán.
_Tránh dùng_: Khoảng lương chào tuyển của một tin, sai số tuyệt đối.

**Nhóm đủ dữ liệu**:
Tổ hợp vai trò nghề nghiệp × cấp bậc có ít nhất 20 tin tuyển dụng trong tập huấn luyện; chỉ nhóm này được hiển thị con số lương dự đoán, nhóm còn lại chỉ hiển thị khoảng lương dự đoán mở rộng kèm cảnh báo ít dữ liệu.
_Tránh dùng_: Vai trò phổ biến, nhóm có trong dữ liệu.
