# #119 — Audit nhãn cấp bậc

Ngày 06/11/2026, baseline `e76cd71`. Chạy độc lập trên ba CSV thô của repository;
không lấy số liệu từ báo cáo prototype kết hợp các ticket sau.

## Kiểm tra nguồn

Nguồn IT Jobs có nhãn cấp bậc; TopCV và CareerBuilder không cung cấp nhãn cho pipeline.
Đếm trên toàn bộ CSV IT Jobs (trước lọc lương/vai trò/khử trùng):

| Nhãn nguồn | Số tin | Cấp bậc suy từ chức danh và kinh nghiệm |
| --- | ---: | --- |
| Intern | 646 | Intern 163; Fresher 210; Junior 251; Middle 1; Senior 5; Lead 6; Manager 10 |
| Trưởng phòng | 321 | Manager 206; Lead 44; Senior 40; Middle 16; Junior 12; Fresher 3 |
| Trưởng nhóm | 273 | Lead 94; Senior 146; Manager 33 |

Không có nhãn nguồn chính xác `Manager`, `Lead`, `Fresher`. Có 115/321 tin
`Trưởng phòng` không có chức danh quản lý theo quy tắc và 179/273 tin `Trưởng nhóm`
không có chức danh Lead. Vì vậy bỏ qua mọi nhãn cấp bậc nguồn, dùng chức danh rồi
số năm kinh nghiệm. Đây là kiểm tra tính nhất quán của nhãn, không phải xác nhận
cấp bậc thực tế bởi người tuyển dụng. `Intern` cần nguyên từ intern hoặc `thực tập`;
`International` không phải Intern; `Head Office` không phải `Head of`.

## Bộ dữ liệu dựng lại

3.809 tin, 685 công ty; train/valid/test = 2.461/652/696, không đổi hàng hay split.
317 tin đổi nhãn. Trong 215 Intern cũ, 31 giữ Intern, 45 thành Fresher, 138 thành
Junior và 1 thành Middle. Mọi Intern mới có dấu hiệu thực tập trong chức danh.

| Cấp bậc | Trước | Sau |
| --- | ---: | ---: |
| Intern | 215 | 31 |
| Fresher | 247 | 285 |
| Junior | 1.285 | 1.433 |
| Middle | 1.167 | 1.169 |
| Senior | 446 | 555 |
| Lead | 306 | 214 |
| Manager | 143 | 122 |

Số tin theo nguồn không đổi: IT Jobs vietnamworks 965, topcv 827, itviec 686,
careerviet 680; TopCV 609; CareerBuilder 42. Một tin `IT Officer (Hanoi Head Office - 621)`
đổi Manager → Junior nhờ sửa ranh giới từ `head of`.

## Huấn luyện và kiểm chứng

Giữ thuật toán, tìm siêu tham số theo valid và ràng buộc kỹ năng ADR 0013.
GradientBoosting được chọn: valid MAE 5.724779; test MAE 5.806721, RMSE 8.557440,
R² 0.741303, MAPE 20.548907%. Đơn vị MAE/RMSE là triệu VND/tháng.
Ngân sách test đặt 5.84 (dư khoảng 0.0333 cho biến thiên số học), thay 5.85 của
bộ nhãn cũ. Không chọn siêu tham số theo test.

Qua `advise`, Backend không kỹ năng, Intern/Fresher 0 năm, Junior 1 năm:

| Thành phố | Intern | Fresher | Junior |
| --- | ---: | ---: | ---: |
| Hà Nội | 5.391 | 10.590 | 12.419 |
| TP. Hồ Chí Minh | 5.774 | 10.810 | 13.501 |

Đây là giá trị dự đoán điểm hiện có, không phải trung vị khảo sát hay phân vị mới.
Test được viết trước sửa và thấy RED cho Intern sai chức danh, nguồn Manager/
Trưởng phòng/Lead/Fresher và Head Office. Sau sửa, dựng dữ liệu, train và validate;
`make check PYTHON=/Users/scara2906/Downloads/ML/.venv/bin/python` pass lint/format
và 53 test (24.33s), gồm các hồi quy cấp bậc và toàn bộ test đơn điệu kỹ năng.
Hai cảnh báo là deprecation Matplotlib từ seaborn.

Giới hạn: Intern chỉ còn 31 tin, nên ước lượng nhóm này ít dữ liệu; thứ tự dự đoán
được kiểm tra cho Backend ở hai thành phố trên, chưa cam kết mọi vai trò. Việc bỏ
nhãn nguồn có thể mất tín hiệu đúng khi chức danh không ghi cấp bậc. Pipeline này
vẫn dự đoán lương chào tuyển, chưa hiệu chuẩn theo lương thị trường bên ngoài.
