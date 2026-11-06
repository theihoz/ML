# Phương pháp

Dự án đi theo 5 bước. Mỗi bước có một file mã nguồn chính trong `job_market/src/career_market/` và một lệnh để chạy lại.

```
Bước 1           Bước 2              Bước 3             Bước 4              Bước 5
Gán nhãn   →   Tạo bộ dữ liệu  →   Huấn luyện   →   Dự đoán & tư vấn  →  Kiểm định
rules.py       dataset.py          training.py       advisor.py          validation.py
```

## Bước 1 – Gán nhãn cho từng tin (`data/rules.py`)

Máy đọc chữ trong tin và suy ra:
- **lương** (thấp, cao, điểm giữa) theo triệu đồng/tháng, đổi đô la và lương năm;
- **vai trò**: một trong 23 vai trò CNTT, theo bộ quy tắc từ khóa xếp từ cụ thể đến chung; tin ngoài ngành (sales, kế toán…) bị bỏ;
- **cấp bậc**: chỉ lấy từ chức danh (Senior, Lead…), không có thì suy từ số năm kinh nghiệm. Không dùng cấp bậc do trang nguồn gắn, vì đo thấy 84% nhãn "Intern" của nguồn là sai;
- **kinh nghiệm**, **khu vực**, **kỹ năng** (69 kỹ năng), **loại công ty**, **hình thức làm việc**.

**Kiểm tra độ chính xác:** lấy mẫu ngẫu nhiên (cố định) rồi duyệt lại từng tin. Mẫu 67 tin ngày 06/11/2026 (AI duyệt): lương 0% sai, vai trò 3%, cấp bậc 1,5%, kỹ năng 2%.

## Bước 2 – Tạo bộ dữ liệu (`data/dataset.py`, lệnh `build-dataset`)

1. Đọc 3 bộ dữ liệu gốc và các lô CSV nhập thêm.
2. **Bỏ 2.400 tin do máy sinh** (đường dẫn `-hist`): chúng làm điểm mô hình đẹp giả.
3. Giữ tin có lương đọc được và thuộc ngành CNTT; tin lô mới không đọc được thì vào **hàng đợi duyệt tay**.
4. Áp dụng **sổ nhãn đã duyệt** (sửa tay của người duyệt).
5. Bỏ tin trùng (cùng chức danh, công ty, lương; hoặc trùng đường dẫn).
6. **Chia theo công ty**: 70% tập học, 15% tập chọn, 15% tập kiểm tra. Mỗi công ty nằm trọn một tập.

Kết quả: 8.523 tin thô → 1.735 tin dùng được.

## Bước 3 – Huấn luyện (`model/estimators.py`, `model/training.py`, lệnh `train`)

1. Biến mỗi tin thành một hàng đặc trưng: vai trò, khu vực, cấp bậc, nền tảng, hình thức, loại công ty, kinh nghiệm, năm, 4 từ khóa chức danh, 69 cột kỹ năng (có/không).
2. Huấn luyện 4 mô hình trên **logarit của lương**: mốc trung vị, Ridge, Random Forest, Gradient Boosting.
3. Mỗi mô hình bị **ràng buộc đơn điệu**: thêm kỹ năng hoặc kinh nghiệm không làm giảm lương (ADR 0013).
4. Thử vài thiết lập, giữ thiết lập sai ít nhất trên **tập chọn**; chọn mô hình tốt nhất cũng theo tập chọn.
5. Chấm một lần trên **tập kiểm tra**; lưu mô hình, sai số, mức quan trọng của đặc trưng, mức tăng lương của kỹ năng.
6. Dựng **hệ số hiệu chỉnh gross** từ báo cáo TopDev và ITviec (ADR 0015).
7. Lưu thành **một phiên bản mới**; chỉ dùng nếu qua **cổng thay model**.

## Bước 4 – Dự đoán và tư vấn (`model/advisor.py`, trang chủ)

1. Nạp mô hình đã lưu (không huấn luyện lại khi người dùng bấm).
2. Dự đoán lương chào tuyển → nhân tỉ lệ p25/p50/p75 → nhân hệ số gross → **khoảng lương**.
3. Nếu nhóm vai trò × cấp bậc có dưới 20 tin học, hoặc trượt chuẩn production → **ẩn con số**, chỉ hiện khoảng rộng hơn.
4. **Gợi ý kỹ năng:** thử thêm từng kỹ năng chưa có (xuất hiện ở ≥ 3% tin cùng vai trò), xếp theo mức tăng lương.
5. **Lộ trình:** dự đoán lại khi thêm 0, 1, 2, 3, 5 năm kinh nghiệm.
6. **Vị trí so với vai trò:** cho biết mức dự đoán cao hơn bao nhiêu % tin cùng vai trò.

## Bước 5 – Kiểm định (`model/validation.py`, `model/production.py`, `model/reality.py`)

| Câu hỏi | Cách kiểm |
|---|---|
| Khoảng lương có đáng tin? | So tỉ lệ tin thật nằm trong khoảng với mức danh nghĩa (50%, 80%, 90%) trên tập kiểm tra |
| Mô hình thắng thật hay nhờ may? | Bootstrap 1.000 lần, bốc lại theo công ty, so theo cặp |
| Có công bằng không? | Độ lệch % theo khu vực, cấp bậc, kinh nghiệm, nền tảng, vai trò, kèm khoảng tin cậy |
| Đủ tốt để dùng thật chưa? | Chuẩn production: trung vị sai số %, tỉ lệ sai ≤ 20%, độ phủ khoảng (ADR 0014) |
| Khớp thực tế không? | So với báo cáo lương TopDev (≤ 15% ở ≥ 80% vai trò) và hồ sơ vàng (≤ 20% ở ≥ 70% hồ sơ) |

## Thêm dữ liệu và huấn luyện lại (lệnh `refresh`)

```
lô CSV → nhập (lưu bất biến) → tạo bộ dữ liệu → huấn luyện thành phiên bản mới → kiểm định → cổng
                                     │                                                       │
                          hàng đợi duyệt tay                                    thay hoặc giữ model cũ
```

Bước nào lỗi thì dừng, model đang dùng giữ nguyên. `versions` liệt kê phiên bản, `rollback` quay lại bản trước.

## Nguyên tắc xuyên suốt

1. **Tập kiểm tra chỉ mở một lần**, không dùng để chọn gì.
2. **Đánh giá trên công ty chưa từng gặp**, vì đó là câu hỏi thật của người dùng.
3. **Nói thật về độ chắc chắn**: khoảng trước, con số sau; ít dữ liệu thì chỉ có khoảng; chưa đạt chuẩn thì ghi "bản thử nghiệm".
4. **Tương quan không phải nhân quả**: mức tăng lương của kỹ năng là phép thử "nếu như", không phải lời hứa.
5. **Mọi quy tắc nằm trong code và có kiểm thử**; notebook chỉ gọi lại để trình bày.
