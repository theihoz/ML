# Các giải pháp của dự án

Mỗi giải pháp được trình bày theo ba phần:

- **Ý tưởng** – gặp vấn đề gì, muốn đạt được điều gì.
- **Phương án** – những cách đã cân nhắc, cách được chọn và vì sao.
- **Cách làm** – làm cụ thể thế nào, nằm ở đâu trong code (đường dẫn tính từ `job_market/src/career_market/`).

Công thức chi tiết của từng bước: [04-cong-thuc.md](04-cong-thuc.md). Lý do của các quyết định lớn: [`docs/adr/`](../adr/).

| # | Giải pháp | Nhóm |
|---|---|---|
| 1 | [Gộp ba nguồn dữ liệu công khai](#1-gộp-ba-nguồn-dữ-liệu-công-khai) | Dữ liệu |
| 2 | [Loại tin do máy sinh ra](#2-loại-tin-do-máy-sinh-ra) | Dữ liệu |
| 3 | [Đọc lương từ chữ](#3-đọc-lương-từ-chữ) | Dữ liệu |
| 4 | [Tin chỉ ghi một con số lương](#4-tin-chỉ-ghi-một-con-số-lương) | Dữ liệu |
| 5 | [Gán vai trò, cấp bậc, kỹ năng bằng quy tắc](#5-gán-vai-trò-cấp-bậc-kỹ-năng-bằng-quy-tắc) | Dữ liệu |
| 6 | [Chia dữ liệu theo công ty](#6-chia-dữ-liệu-theo-công-ty) | Đánh giá |
| 7 | [Chọn mô hình](#7-chọn-mô-hình) | Mô hình |
| 8 | [Thêm kỹ năng không làm giảm lương](#8-thêm-kỹ-năng-không-làm-giảm-lương) | Mô hình |
| 9 | [Khoảng lương thay cho một con số](#9-khoảng-lương-thay-cho-một-con-số) | Tư vấn |
| 10 | [Ẩn con số khi ít dữ liệu](#10-ẩn-con-số-khi-ít-dữ-liệu) | Tư vấn |
| 11 | [Quy về lương gross thị trường](#11-quy-về-lương-gross-thị-trường) | Tư vấn |
| 12 | [Gợi ý kỹ năng nên học](#12-gợi-ý-kỹ-năng-nên-học) | Tư vấn |
| 13 | [Kiểm định độ tin cậy và chuẩn production](#13-kiểm-định-độ-tin-cậy-và-chuẩn-production) | Kiểm chứng |
| 14 | [Đối chiếu với báo cáo lương bên ngoài](#14-đối-chiếu-với-báo-cáo-lương-bên-ngoài) | Kiểm chứng |
| 15 | [Phiên bản model, cổng thay và quay lại](#15-phiên-bản-model-cổng-thay-và-quay-lại) | Vận hành |
| 16 | [Thêm dữ liệu mới và duyệt tay](#16-thêm-dữ-liệu-mới-và-duyệt-tay) | Vận hành |
| 17 | [Giao diện web](#17-giao-diện-web) | Ứng dụng |
| 18 | [Demo chạy không cần mạng](#18-demo-chạy-không-cần-mạng) | Ứng dụng |
| 19 | [Kiểm thử tự động và notebook](#19-kiểm-thử-tự-động-và-notebook) | Chất lượng |

---

## Dữ liệu

### 1. Gộp ba nguồn dữ liệu công khai

**Ý tưởng.** Muốn dự đoán lương cần nhiều tin tuyển dụng có ghi lương; một nguồn đơn lẻ quá ít và lệch về một trang.

**Phương án.**
- Tự thu thập (crawl) các trang tuyển dụng → *không chọn*: chưa rõ điều khoản cho phép của từng trang (#103), tốn thời gian.
- Dùng bộ dữ liệu khảo sát lương → *không chọn*: không có bộ công khai đủ chi tiết cho Việt Nam.
- **Gộp ba bộ dữ liệu công khai trên Kaggle** (TopCV 2026, IT Jobs 2026, CareerBuilder 2023) → *chọn*: hợp pháp, giấy phép rõ ràng (CC0, CC BY, MIT), đủ 8.523 tin.

**Cách làm.** Mỗi nguồn có một hàm đọc riêng (`_topcv`, `_it_posts`, `_careerbuilder` trong `data/dataset.py`), đưa mọi tin về **cùng một dạng** (tiêu đề, công ty, địa điểm, chuỗi lương, kinh nghiệm, kỹ năng…). Phần xử lý phía sau không cần biết tin đến từ nguồn nào. File gốc giữ nguyên trong `datasets/raw/`, kèm nguồn và giấy phép trong `datasets/README.md`.

### 2. Loại tin do máy sinh ra

**Ý tưởng.** Ngày đăng tin ở ba trang rải đều 2018–2025, điều không thể có ở thị trường thật. Điều tra thêm thì thấy 2.400 tin (đúng 800 tin mỗi trang) là tin giả: đường dẫn chứa `-hist`, kỹ năng ngẫu nhiên, không có mô tả. Tin giả dễ đoán nên làm điểm mô hình đẹp giả.

**Phương án.**
- Giữ lại, chỉ sửa cột ngày → *không chọn*: kỹ năng và lương vẫn giả.
- Giữ lại nhưng đánh dấu → *không chọn*: mô hình vẫn học từ dữ liệu giả.
- **Loại hẳn** → *chọn*: mục tiêu là đoán lương của tin thật. Cái giá: mất hơn nửa dữ liệu, sai số tăng nhưng trung thực.

**Cách làm.** Hàm `is_synthetic(url)` trong `data/rules.py` nhận ra đường dẫn dạng `-hist` + 9 chữ số; `build_dataset` bỏ các tin này **trước** khi đọc lương và đếm vào phễu (`synthetic_removed`). Có kiểm thử chặn để tin giả không quay lại.

### 3. Đọc lương từ chữ

**Ý tưởng.** Lương được ghi theo hơn 30 kiểu ("15–25 triệu", "Tới 30 triệu", "$1.000", "200tr–500tr/năm", "Thỏa thuận"). Mô hình cần **một con số** theo cùng đơn vị.

**Phương án.**
- Lấy mức thấp → thiên thấp; lấy mức cao → giống "mức trần".
- **Lấy điểm giữa của khoảng** → *chọn*: gần với câu nói thường gặp "lương khoảng 20 triệu".
- Với khoảng quá rộng (ví dụ "1–40 triệu" là giá trị điền sẵn của biểu mẫu) → **bỏ** khi mức cao gấp hơn 3 lần mức thấp.

**Cách làm.** Hàm `parse_salary` trong `data/rules.py`: tách các con số, đổi đô la theo tỷ giá năm đăng tin, chia 12 với lương năm, đổi đồng sang triệu, bỏ tin "thỏa thuận", bỏ khoảng gấp hơn 3 lần, chỉ giữ lương 3–150 triệu/tháng. Kết quả là `(thấp, cao, điểm giữa)`.

### 4. Tin chỉ ghi một con số lương

**Ý tưởng.** Khoảng một phần mười số tin chỉ ghi "Tới X" hoặc "Từ X"; phải đoán đầu còn lại để lấy điểm giữa.

**Phương án.** Đã so ba cách trên cùng dữ liệu (`docs/research/118-single-salary-rules.md`):
- Hệ số cố định ×0,7 / ×1,3 (`expand30`).
- Dùng đúng con số đó làm nhãn (`point`) → kém nhất ở mọi chỉ số.
- **Tỉ lệ cao/thấp theo thói quen của từng trang**, học từ tin ghi đủ hai đầu (`ratio`) → *chọn*: trung vị sai số thấp nhất, tỉ lệ được ước lượng từ dữ liệu thay vì đặt tay.

**Cách làm.** `_one_sided_ratios` trong `data/dataset.py` tính trung vị tỉ lệ cao/thấp của các tin ghi đủ hai đầu **trong tập học**, theo từng nguồn (dưới 30 tin thì dùng trung vị chung). Sau đó tính lại lương cho các tin một con số. Đổi quy tắc bằng `build-dataset --single-salary-rule`.

### 5. Gán vai trò, cấp bậc, kỹ năng bằng quy tắc

**Ý tưởng.** Mỗi tin cần biết thuộc vai trò nào (trong 23 vai trò CNTT), cấp bậc gì, đòi kỹ năng gì, để mô hình học và để tư vấn.

**Phương án.**
- Gán tay toàn bộ → không khả thi với hàng nghìn tin.
- Dùng mô hình ngôn ngữ (AI) gán → khó kiểm chứng, khó chạy lại cho kết quả giống hệt.
- **Bộ quy tắc từ khóa, minh bạch, có kiểm thử**, rồi **đo độ chính xác bằng mẫu duyệt** → *chọn*.
- Cấp bậc: **chỉ lấy từ chức danh**, không dùng nhãn cấp bậc của trang nguồn, vì đo thấy 84% nhãn "Intern" của nguồn là sai (#119).

**Cách làm.** `data/rules.py`: `classify_role` duyệt danh sách quy tắc từ cụ thể đến chung, loại tin ngoài ngành (sales, kế toán…); `derive_level` đọc chức danh (Senior, Lead…), không có thì suy từ số năm; `extract_skills` dò 69 kỹ năng, bỏ ngoại ngữ chỉ nhắc ở phần phúc lợi. Mẫu kiểm tra 67 tin (AI duyệt) cho tỉ lệ sai: lương 0%, vai trò 3%, cấp bậc 1,5%, kỹ năng 2%; lỗi lặp lại được sửa thẳng vào quy tắc.

---

## Đánh giá

### 6. Chia dữ liệu theo công ty

**Ý tưởng.** Một công ty đăng hàng chục tin gần giống nhau. Nếu chia ngẫu nhiên từng tin, mô hình chỉ cần "nhớ" công ty là đoán đúng, điểm cao giả. Người dùng thật lại hay hỏi về công ty mới.

**Phương án.**
- Chia ngẫu nhiên theo tin → *không chọn*: rò rỉ thông tin công ty.
- Chia theo thời gian → *không chọn*: ngày đăng của dữ liệu không tin cậy.
- **Chia theo công ty** (70% học, 15% chọn, 15% kiểm tra) → *chọn* (ADR 0008).

**Cách làm.** `_split_for` trong `data/dataset.py` băm tên công ty (SHA-256, hạt giống 42) thành một số từ 0 đến 1 rồi xếp vào tập. Cùng công ty luôn vào cùng tập, chạy lại bao nhiêu lần cũng ra cùng cách chia; tin mới của công ty đã có trong tập học cũng vào tập học.

---

## Mô hình

### 7. Chọn mô hình

**Ý tưởng.** Cần một mô hình đoán lương đủ tốt, giải thích được và chạy nhanh với khoảng 1.700 tin.

**Phương án.** So bốn ứng viên, giống bốn cách con người ước lượng lương:
- Mốc trung vị (ai hỏi cũng trả lời một con số) → làm mức tối thiểu.
- Ridge (bảng cộng điểm).
- Random Forest (trung bình nhiều cây).
- **Gradient Boosting** (chuỗi cây sửa lỗi nối tiếp) → *được chọn* vì sai ít nhất trên tập chọn.
- Mạng nơ-ron / mô hình lớn → *không thử*: quá ít dữ liệu, khó giải thích.

**Cách làm.** `model/estimators.py` dựng 4 mô hình; `model/training.py` thử vài thiết lập cho mỗi mô hình, giữ thiết lập có MAE nhỏ nhất trên **tập chọn**, chọn mô hình tốt nhất cũng theo tập chọn, rồi chấm **một lần** trên tập kiểm tra. Mô hình học trên **logarit của lương** để quan tâm sai số theo tỉ lệ. Không đưa tên công ty vào để mô hình dùng được cho công ty mới.

### 8. Thêm kỹ năng không làm giảm lương

**Ý tưởng.** Mô hình từng cho kết quả vô lý: thêm Java vào hồ sơ Backend 5 năm làm lương giảm từ 47,7 xuống 42,3 triệu. Nguyên nhân: tin liệt kê nhiều kỹ năng thường là tin tuyển người mới, lương thấp.

**Phương án.**
- Giữ nguyên, chỉ cảnh báo → lời khuyên vẫn vô lý.
- Ép mỗi kỹ năng cộng một mức tối thiểu → bịa số.
- **Bỏ đặc trưng "số kỹ năng" và buộc mô hình đơn điệu theo kỹ năng và kinh nghiệm** → *chọn* (ADR 0013): kỹ năng không có bằng chứng thì cộng gần 0, không bao giờ trừ.

**Cách làm.** `model/estimators.py`: Gradient Boosting dùng ràng buộc đơn điệu có sẵn (`monotonic_cst`); Ridge giải bài toán có chặn hệ số kỹ năng ≥ 0 (`SignedRidge`); Random Forest được bọc "bao đơn điệu" (`SkillEnvelope`: lấy mức cao nhất trên mọi tập con kỹ năng). Kiểm thử thử thêm từng kỹ năng trên nhiều hồ sơ để chặn lỗi quay lại.

---

## Tư vấn

### 9. Khoảng lương thay cho một con số

**Ý tưởng.** Lương thật dao động rộng; một con số duy nhất tạo cảm giác chắc chắn giả và dễ bị cho là "sai".

**Phương án.**
- Chỉ hiện một con số → *không chọn*.
- Hiện khoảng tin cậy thống kê → khó hiểu với người không chuyên.
- **Hiện khoảng p25 – trung vị – p75, khoảng trước, con số sau** (giống LinkedIn Salary) → *chọn*.

**Cách làm.** Khi huấn luyện, tính tỉ lệ *lương thật / dự đoán* trên tập chọn và lấy phân vị 25, 50, 75 (`model/training.py`). Khi tư vấn, nhân dự đoán với các tỉ lệ này (`model/advisor.py`). Trang tư vấn hiện "Khoảng lương" trước, "Mức điển hình" sau.

### 10. Ẩn con số khi ít dữ liệu

**Ý tưởng.** Với nhóm hiếm (ví dụ Data Engineer cấp Middle chỉ 7 tin), con số dự đoán không đáng tin; đưa ra là đánh lừa người dùng.

**Phương án.**
- Vẫn hiện con số, kèm cảnh báo nhỏ → người dùng thường bỏ qua cảnh báo.
- **Không hiện con số, chỉ hiện khoảng rộng hơn kèm lý do bằng lời thường** → *chọn*. Ngưỡng 20 tin theo cách LinkedIn làm.

**Cách làm.** `model/support.py` lưu số tin học theo vai trò × cấp bậc và khoảng mở rộng cho từng nhóm. `resolve` quyết định: đủ 20 tin và không trượt chuẩn production thì hiện con số; nếu không thì chỉ hiện khoảng p10–p90 của nhóm. Trang tư vấn cũng ẩn mức tăng lương của từng kỹ năng với hồ sơ ít dữ liệu.

### 11. Quy về lương gross thị trường

**Ý tưởng.** Mô hình học từ lương ghi trên tin tuyển dụng, chưa rõ gross hay net; người dùng muốn biết "mình đáng được trả bao nhiêu".

**Phương án.**
- Huấn luyện thẳng trên số liệu khảo sát → *không chọn*: trộn hai đại lượng khác nhau, khảo sát không có chi tiết từng tin.
- **Giữ mô hình học từ tin, rồi nhân một hệ số hiệu chỉnh theo báo cáo lương** → *chọn* (ADR 0015): đơn giản, giải thích được.

**Cách làm.** `model/calibration.py` tính hệ số hai bước khi huấn luyện: (1) theo cấp bậc × thành phố, so trung bình gross TopDev với trung bình dự đoán; (2) theo vai trò, so trung vị ITviec với trung vị dự đoán sau bước 1. Hệ số được lưu cùng mô hình (`calibration.json`) kèm mã băm để không dùng nhầm phiên bản. Thiếu ô thì dùng hệ số cấp bậc chung; Intern mượn hệ số Fresher và có cảnh báo.

### 12. Gợi ý kỹ năng nên học

**Ý tưởng.** Người dùng hỏi "học gì để tăng lương", không phải "cái gì đang phổ biến".

**Phương án.**
- Xếp theo độ phổ biến → trả lời sai câu hỏi.
- **Thử thêm từng kỹ năng vào hồ sơ và đo lương dự đoán tăng bao nhiêu** (phép thử "nếu như") → *chọn* (ADR 0009). Thiếu gợi ý thì bổ sung kỹ năng được tuyển nhiều, ghi rõ lý do.

**Cách làm.** `advise` trong `model/advisor.py`: chỉ xét kỹ năng chưa có và xuất hiện ở ≥ 3% tin cùng vai trò; bật đúng một kỹ năng, dự đoán lại, nhân hệ số gross; xếp theo mức tăng, lấy 5 kỹ năng đầu. Kèm **lộ trình**: dự đoán lại khi thêm 0, 1, 2, 3, 5 năm kinh nghiệm. App luôn ghi rõ đây là tương quan, không phải lời hứa.

---

## Kiểm chứng

### 13. Kiểm định độ tin cậy và chuẩn production

**Ý tưởng.** Một con số sai số trung bình không cho biết khoảng lương có đáng tin, mô hình thắng thật hay nhờ may, có thiên vị ai, và đã đủ tốt để dùng chưa.

**Phương án.**
- Chỉ báo MAE → thiếu.
- **Bốn phép kiểm tra, theo cách các trang lương lớn (Glassdoor, LinkedIn) công bố** → *chọn* (ADR 0014).

**Cách làm.** `model/validation.py` và `model/production.py`:
- **Hiệu chuẩn:** khoảng 50/80/90% có chứa đúng tỉ lệ lương thật như vậy không.
- **Bootstrap:** bốc lại các công ty 1.000 lần để xem mô hình thắng ổn định không.
- **Công bằng:** độ lệch % theo khu vực, cấp bậc, kinh nghiệm, nền tảng, vai trò, kèm khoảng tin cậy.
- **Chuẩn production:** trung vị sai số ≤ 15%, ≥ 65% dự đoán lệch ≤ 20%, khoảng 80% phủ 75–85%; chấm theo kết quả xấu nhất hợp lý để không "đậu nhờ may".

Mô hình hiện **chưa đạt** chuẩn; app ghi rõ "bản thử nghiệm" và "kết quả mang tính tham khảo".

### 14. Đối chiếu với báo cáo lương bên ngoài

**Ý tưởng.** Điểm số trên tập kiểm tra chỉ cho biết mô hình khớp lương **ghi trên tin**. Cần biết thêm có khớp lương **người đi làm thật** không.

**Phương án.**
- Tự khảo sát lương → ngoài khả năng của nhóm.
- **So với báo cáo lương công bố (TopDev, ITviec)** theo đúng độ chi tiết báo cáo có → *chọn*. Không lấp ô thiếu, không coi trung bình là trung vị.

**Cách làm.** Số liệu báo cáo kèm nguồn, năm, trang trong `datasets/reference/salary_reference.csv`. `model/reality.py` lấy trung vị lương dự đoán (đã quy gross) theo từng vai trò và so với báo cáo: đạt khi lệch ≤ 15% ở ≥ 80% vai trò. Hiện **8/10** vai trò đạt. Mốc đã dùng để tính hệ số được báo riêng, không tính là bằng chứng độc lập.

---

## Vận hành

### 15. Phiên bản model, cổng thay và quay lại

**Ý tưởng.** Huấn luyện lại có thể làm mô hình kém đi; cần giữ lại các bản cũ và quay về được ngay khi có sự cố.

**Phương án.**
- Ghi đè mô hình mỗi lần huấn luyện → *không chọn*: mất bản cũ.
- **Mỗi lần huấn luyện là một phiên bản riêng; một con trỏ chỉ bản đang dùng; chỉ đổi con trỏ khi qua cổng kiểm tra** → *chọn*.

**Cách làm.** `model/versions.py`: `retrain_version` huấn luyện vào thư mục mới trong `artifacts/`, kiểm định, chấm lại bản đang dùng trên cùng dữ liệu, rồi hỏi `decide` (`model/promotion.py`): thay khi bản mới đạt chuẩn, hoặc cả hai chưa đạt mà bản mới không kém ở chỉ số chung nào. Con trỏ là file `artifacts/CURRENT`. Lệnh `make versions`, `make load` (nạp bản vừa train), `make rollback` (quay lại). App hiện dòng độ mới: phiên bản, ngày cập nhật, số tin học, trạng thái chuẩn.

### 16. Thêm dữ liệu mới và duyệt tay

**Ý tưởng.** Mô hình chỉ tốt lên khi có thêm dữ liệu thật; người quản trị cần đưa tin mới vào mà không phải sửa code, và tin máy không hiểu không được mất.

**Phương án.**
- Thêm file vào `datasets/raw` và sửa code đọc → *không chọn*: mỗi lần một sửa.
- **Nhập lô CSV theo mẫu cố định, chạy cả chuỗi bằng một lệnh, tin khó đưa vào danh sách chờ người duyệt** → *chọn*.

**Cách làm.**
- `data/batches.py`: kiểm tra từng dòng, báo dòng lỗi kèm lý do, lưu lô **bất biến** kèm mã băm; nhập trùng không tạo lô mới.
- `data/dataset.py`: đọc thêm mọi lô, bỏ tin trùng đường dẫn với tin đã có, đưa tin lương "thỏa thuận"/bất thường hoặc không rõ vai trò vào `review_queue.csv`.
- `data/review.py`: **sổ nhãn đã duyệt** (`datasets/labels/reviewed.csv`), áp dụng ở lần dựng sau, kiểm tra nhãn ghi tay phải đúng từ vựng.
- `refresh.py` (`make refresh CSV=…`): nhập → dựng → huấn luyện → kiểm định → cổng; bước nào lỗi thì dừng, mô hình đang dùng giữ nguyên.

---

## Ứng dụng

### 17. Giao diện web

**Ý tưởng.** Người không biết lập trình cũng dùng được: nhập hồ sơ, xem kết quả, xem dữ liệu và độ tin cậy.

**Phương án.**
- Web đầy đủ (HTML/JavaScript + API) → tốn công, ngoài phạm vi môn Python.
- **Streamlit, viết web bằng Python thuần** → *chọn* (ADR 0001).

**Cách làm.** `app.py` khai báo 5 trang trong `pages/`: Tư vấn (trang chủ), Tổng quan, Thị trường, Đánh giá, Dữ liệu. `ui/cache.py` nạp dữ liệu, mô hình và vẽ biểu đồ đúng một lần; `ui/charts.py` dùng chung biểu đồ cho web, notebook và báo cáo. Không huấn luyện lại khi người dùng bấm: cùng hồ sơ luôn ra cùng kết quả. Hồ sơ chia sẻ được qua đường dẫn (`/?role=…&years=…&skills=…`). Số liệu khó hiểu được viết bằng chữ, ví dụ "Cao hơn 36% tin" thay cho "P36".

### 18. Demo chạy không cần mạng

**Ý tưởng.** Ngày thuyết trình có thể mất mạng hoặc máy khác thiếu thư viện.

**Phương án.**
- Cài Python và thư viện trên máy demo → dễ hỏng.
- **Đóng gói ứng dụng, dữ liệu và mô hình vào một image Docker, kiểm tra trước khi mở** → *chọn* (ADR 0004).

**Cách làm.** `Dockerfile` + `docker-compose.yaml`; `docker/check_demo.py` kiểm tra đủ dữ liệu, 4 mô hình, hệ số hiệu chỉnh, bảng đối chiếu và chạy thử một dự đoán **trước** khi mở web. Ngày demo chỉ cần `docker compose up -d --wait --no-build --pull never` (xem `docs/DEMO.md`).

---

## Chất lượng

### 19. Kiểm thử tự động và notebook

**Ý tưởng.** Sửa chỗ này dễ làm hỏng chỗ khác; người chấm cần thấy được logic phía sau từng tính năng.

**Phương án.**
- Kiểm tra bằng tay trước mỗi lần nộp → dễ sót.
- **Kiểm thử tự động cho từng lỗi đã gặp + notebook trình bày từng tính năng, chạy tự động trong CI** → *chọn*.

**Cách làm.** `job_market/tests/` (hơn 200 kiểm thử): thêm kỹ năng không giảm lương, không còn tin giả, hồ sơ ít dữ liệu không hiện con số, khoảng lương đúng thứ tự, phiên bản và quay lại… `make check` chạy lint + kiểm thử; GitHub Actions chạy lại mỗi lần đẩy code. 7 notebook trong `job_market/notebooks/` chỉ gọi lại code thư viện, được lưu không kèm kết quả chạy và được CI chạy thử từ đầu đến cuối.

---

## Giới hạn hiện tại (nói thật)

| Giới hạn | Hướng xử lý tiếp |
|---|---|
| Chỉ 1.735 tin thật; tập kiểm tra 288 tin | Nhập thêm lô tin thật bằng `make refresh` |
| Chưa đạt chuẩn production (cấp Lead trượt) | Thêm dữ liệu, thêm thông tin quy mô công ty |
| Lương gross chỉ quy đổi gần đúng từ báo cáo | Thu thập lương thật của người đi làm để kiểm tra độc lập |
| Nhãn mới được AI duyệt, chưa có người duyệt | Mời người duyệt lại mẫu kiểm tra |
| Chưa tự thu thập tin mới (crawler) | Chờ xác nhận điều khoản thu thập (#103, #110) |
