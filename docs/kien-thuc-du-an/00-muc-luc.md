# Kiến thức dự án – mục lục

Bộ tài liệu này giải thích **dự án dự đoán lương CNTT** dùng gì, gọi các khái niệm là gì, làm theo cách nào và tính bằng công thức nào. Viết cho người đọc không chuyên kỹ thuật; mỗi khái niệm đều có ví dụ đời thường.

| Thứ tự đọc | File | Trả lời câu hỏi |
|---|---|---|
| 1 | [01-cong-nghe.md](01-cong-nghe.md) | Dự án được làm bằng công cụ gì, vì sao chọn công cụ đó? |
| 2 | [02-thuat-ngu.md](02-thuat-ngu.md) | Các từ chuyên môn trong app, notebook và slide nghĩa là gì? |
| 3 | [03-phuong-phap.md](03-phuong-phap.md) | Từ tin tuyển dụng thô đến lời tư vấn lương đi qua những bước nào? |
| 4 | [04-cong-thuc.md](04-cong-thuc.md) | Mỗi con số trên app được tính bằng công thức nào, nằm ở đâu trong code? |
| 5 | [05-giai-phap.md](05-giai-phap.md) | Dự án giải quyết từng vấn đề thế nào: ý tưởng, phương án đã cân nhắc, cách làm? |

## Đọc nhanh trong 1 phút

- **Dữ liệu:** 1.735 tin tuyển dụng CNTT thật có ghi lương, từ ba bộ dữ liệu công khai trên Kaggle (TopCV, VietnamWorks, ITviec, CareerViet, CareerBuilder).
- **Mô hình:** Gradient Boosting, học từ vai trò, khu vực, cấp bậc, kinh nghiệm, kỹ năng… Sai trung bình khoảng 6,5 triệu đồng/tin trên những công ty chưa từng gặp.
- **Kết quả cho người dùng:** một **khoảng lương** gross thị trường gần đúng, kèm mức điển hình (khi đủ dữ liệu), 5 kỹ năng nên học và lộ trình theo kinh nghiệm.
- **Độ tin cậy:** khớp báo cáo lương TopDev ở 8/10 vai trò (sai ≤ 15%), nhưng **chưa đạt chuẩn production**; app ghi rõ "bản thử nghiệm".

## Tài liệu liên quan

- [`GLOSSARY.md`](../../GLOSSARY.md): định nghĩa chuẩn của thuật ngữ nghiệp vụ (nơi gốc; file 02 dẫn sang khi trùng).
- [`docs/STRUCTURE.md`](../STRUCTURE.md): bố cục mã nguồn.
- [`docs/adr/`](../adr/): lý do của từng quyết định lớn (ADR 0008 chia theo công ty, 0013 lương đơn điệu theo kỹ năng, 0014 chuẩn production, 0015 hiệu chỉnh gross).
- [`docs/DEMO.md`](../DEMO.md): cách chạy và thao tác demo.
