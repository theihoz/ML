# Quy tắc cho tin chỉ ghi một con số lương (#118)

Ngày 06/11/2026. Khoảng một phần mười tin chỉ ghi một đầu lương ("Tới 30 triệu", "Từ 15 triệu"). Ba cách suy đầu còn lại được so trên cùng bộ dữ liệu 1.735 tin thật, cùng split theo công ty, cùng lưới siêu tham số chọn theo valid; mỗi lần dựng lại dữ liệu, huấn luyện, hiệu chỉnh và kiểm định từ đầu. Bảng máy đọc: `job_market/artifacts/salary-v2/single_salary_rules.json`.

| Quy tắc | Định nghĩa | MAE test | Bộ đối chiếu | Độ lệch TB đối chiếu | Trung vị sai số % | Sai ≤ 20% |
|---|---|---:|---:|---:|---:|---:|
| **ratio** | Tỉ lệ cao/thấp trung vị của tin ghi đủ hai đầu cùng nguồn (#81) | 6,489 | 8/10 | 9,77% | **16,86** | 55,2% |
| expand30 | Tới X: [0,7X; X]; Từ X: [X; 1,3X] | 6,453 | 8/10 | 9,77% | 17,14 | 56,9% |
| point | Dùng đúng X làm nhãn | 6,563 | 8/10 | 9,77% | 18,19 | 56,3% |

**Bộ đối chiếu không phân biệt được ba quy tắc.** Hiệu chỉnh hai bước (cấp bậc × thành phố, rồi theo vai trò, ADR 0015) kéo trung vị mỗi vai trò về cùng mốc nên độ lệch giống hệt nhau. Tiêu chí của ticket ("độ lệch đối chiếu thấp hơn") vì vậy hoà; quyết định dựa trên chỉ số chính của chuẩn production (trung vị sai số %, ADR 0014) đo trên tập test.

**Chọn `ratio`** (giữ mặc định): trung vị sai số thấp nhất, và tỉ lệ được ước lượng từ dữ liệu thay vì một hằng số. `point` kém nhất ở mọi chỉ số. Chênh giữa `ratio` và `expand30` nhỏ (0,28 điểm % trung vị sai số, 0,04 triệu MAE theo chiều ngược lại) và chưa có kiểm định thống kê: đây là lựa chọn mặc định hợp lý, không phải ưu thế đã chứng minh. Sau khi dựng lại, tiêu chí bộ đối chiếu vẫn đạt (8/10 ô sai ≤ 15%).

Chạy lại đối chứng: `python -m career_market build-dataset --single-salary-rule expand30` (hoặc `point`), rồi `train`, `validate`, `reality-check`.
