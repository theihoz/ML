# Độ chính xác của bộ gán nhãn tự động (#79)

Ngày 06/11/2026. Ticket #79 trong bản đồ #76.

> **Lưu ý:** mẫu này do **AI (Claude) duyệt** theo yêu cầu của chủ dự án, không phải người duyệt. Kết quả là ước lượng ban đầu. Nên có người duyệt lại ít nhất các dòng có ghi chú trước khi dùng làm số liệu chính thức. File duyệt dùng chung định dạng, nên người duyệt chỉ cần sửa các cột `review_*` rồi chạy lại `score_review`.

## Cách làm

- **Lấy mẫu:** `career_market.label_review.review_sample(size=200, seed=42)` lấy mẫu phân tầng theo nguồn, tỉ lệ thuận với số tin, mỗi nguồn ít nhất 10 tin, rồi rải đều theo vai trò. Kết quả là 208 tin, đủ 23 vai trò, gồm 51 VietnamWorks, 43 TopCV, 36 ITviec, 36 CareerViet (bộ IT Jobs 2026), 32 TopCV 2026 và 10 CareerBuilder 2023.
- **Dữ liệu người duyệt xem:** mỗi dòng đặt nhãn tự động cạnh dữ liệu thô, gồm chuỗi lương, chuỗi kinh nghiệm, cấp bậc của nguồn, và đoạn văn quanh chỗ khớp của từng kỹ năng.
- **Tiêu chí chấm:**
  - Lương: chuỗi lương được đọc đúng theo quy tắc của ADR 0003/0007.
  - Vai trò: đúng với chức danh.
  - Cấp bậc: khi chức danh ghi rõ cấp bậc thì cấp bậc trong chức danh được ưu tiên.
  - Kinh nghiệm: đọc đúng chuỗi kinh nghiệm; nguồn không ghi thì bỏ qua.
  - Kỹ năng: chỉ chấm độ chính xác (kỹ năng được gán có đúng là kỹ năng đó không). Không chấm kỹ năng bị bỏ sót.
- File duyệt: `job_market/datasets/labels/2026-11-06/label_accuracy_review.csv`.

## Kết quả

| Nhãn | Số dòng chấm | Đúng | Tỉ lệ đúng |
|---|---|---|---|
| Lương (đọc chuỗi) | 208 | 208 | 100% |
| Kinh nghiệm (năm) | 204 | 204 | 100% |
| Vai trò | 208 | 198 | 95.2% |
| Cấp bậc | 208 | 197 | 94.7% |
| Kỹ năng (độ chính xác) | 504 kỹ năng được gán | 497 | 98.6% |

Theo nguồn, VietnamWorks kém nhất: vai trò đúng 90.2%, cấp bậc đúng 84.3%.

### Lỗi theo loại

**Vai trò (10 lỗi):**
- 3 tin không phải nghề CNTT lọt vào: tư vấn bán hàng mảng game, pháp chế mảng game, vận hành máy phay CNC.
- 1 tin chỉ huy trưởng công trường bị gán Quản lý dự án.
- MERN/MEAN stack bị gán Software Engineer (chung) thay vì Fullstack (3 tin).
- 1 tin Game Artist bị gán Game Developer.
- 1 tin Helpdesk bị gán Quản trị hệ thống.
- 1 tin QC cho data platform bị gán Data Engineer.

**Cấp bậc (11 lỗi):**
- Cấp bậc của nguồn đè lên cấp bậc ghi trong chức danh: "Senior …" có nguồn ghi "Trưởng nhóm" thành Lead (4 tin); "Technical Lead" có nguồn ghi "Trưởng phòng" thành Manager.
- "Product Manager" bị coi là cấp Manager (3 tin).
- Chức danh ghi Junior nhưng nguồn ghi Intern hoặc Mới tốt nghiệp (2 tin).
- Cấp bậc nguồn là Intern trong khi yêu cầu 2 năm kinh nghiệm (1 tin).

**Kỹ năng (7 lỗi):**
- "API Testing", "OpenAI API", "LLM API" bị khớp thành REST API (6 lỗi).
- "Tiếng Nhật" nằm ở phần phúc lợi nhưng bị coi là yêu cầu (1 lỗi).

## Phát hiện ngoài phạm vi bộ gán nhãn

- **Lương đọc đúng nhưng vẫn có thể lệch thật.** 9/208 tin (4.3%) chỉ ghi một đầu ("Tới X"), nên đầu thấp được suy ra bằng ×0.7. Có tin "Từ 30 triệu" mà chức danh ghi đúng 30tr/tháng, nhưng nhãn thành 30–39. Đây là nhiễu nhãn đã đo ở #77, không phải lỗi đọc chuỗi.
- **Chất lượng nguồn IT Jobs 2026.** Danh sách kỹ năng của nguồn nhiều chỗ không khớp chức danh: Android Developer có TypeScript, Swift, React; DBA có Tableau; .NET Developer có Java/Spring. Ngoài ra, nhiều chức danh lặp lại nguyên mẫu ("Database Administrator", "QA Tech Lead", "Engineering Manager"), và khoảng lương là các cặp số tròn hẹp. Bộ gán nhãn trích đúng những gì nguồn ghi, nên lỗi này không tính vào độ chính xác. Nhưng nó khiến cột kỹ năng của bộ này đáng tin kém. Đây là dấu hiệu cần kiểm tra xem bộ này có phải dữ liệu tổng hợp hay không, trước khi dựa vào nó để thêm đặc trưng (#81).
- **Phạm vi chưa đo:** recall của kỹ năng (kỹ năng có trong JD nhưng bị bỏ sót), vì phải đọc toàn bộ JD.

## Ý nghĩa cho #81

Bộ gán nhãn không phải nút thắt chính của sai số: lương và kinh nghiệm đọc đúng 100%, vai trò và cấp bậc đúng khoảng 95%. Các sửa nhỏ có lợi:
- Ưu tiên cấp bậc ghi trong chức danh hơn cấp bậc của nguồn.
- "Product Manager" không phải cấp Manager.
- MERN/MEAN là Fullstack.
- Loại các tin không phải nghề CNTT.
- "API" đơn lẻ không phải REST API.

Đáng chú ý hơn là chất lượng nguồn IT Jobs 2026, vì nguồn này chiếm 83% số tin có nhãn.
