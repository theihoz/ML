# Chuẩn production cho dự đoán lương chào tuyển

Ngày 06/11/2026, người dùng muốn đưa trang tư vấn salary-v2 cho người dùng thật. Trước đó dự án chỉ có tiêu chí phát hành "thắng baseline trên validation và test" (ADR 0008), không có ngưỡng độ chính xác, và mọi hồ sơ đều nhận một con số lương như nhau. Qua ticket #78, người dùng chọn đặt chuẩn production theo cách các sản phẩm dự đoán lương thực tế đang làm, thay vì tự đặt một ngưỡng MAPE.

## Tham chiếu

- Glassdoor (Local Pay Reports Methodology, 2016) công bố độ chính xác bằng trung vị sai số (10.2%) và tỉ lệ dự đoán sai không quá 20% (75.3%), và không hiện ước tính khi thiếu dữ liệu.
- LinkedIn Salary (blog kỹ thuật 2017, arXiv 1703.09845) hiển thị phân vị 10, trung vị và phân vị 90. Nhóm có từ 20 mẫu dùng phân vị thực nghiệm; nhóm nhỏ hơn được làm mượt.

Cả hai dựa trên lương thực nhận và có thông tin công ty. Dự án chỉ có **Lương chào tuyển** và chưa có đặc trưng công ty, nên mức của Glassdoor là mục tiêu dài hạn, không phải điều kiện lên production.

## Quyết định

**Chỉ số.** Bỏ MAPE làm chỉ số cổng. Dùng ba chỉ số:
- trung vị sai số %;
- tỉ lệ dự đoán sai không quá 20%;
- độ phủ của **Khoảng lương dự đoán** p10–p90.

**Ngưỡng:**

| Phạm vi | Trung vị sai số | Tỉ lệ sai ≤ 20% | Độ phủ p10–p90 | So bằng |
|---|---|---|---|---|
| Toàn bộ tập test | ≤ 15% | ≥ 65% | 75–85% | cận bất lợi bootstrap 95% |
| Mỗi vai trò, mỗi cấp bậc có ≥ 20 tin test | ≤ 20% | ≥ 50% | ≥ 70% | giá trị điểm |
| Mục tiêu dài hạn (không phải điều kiện) | ≤ 10% | ≥ 75% | — | cận bất lợi bootstrap 95% |

**Cách kiểm.** Kiểm trên tập test tách theo công ty (ADR 0008). Bootstrap 1000 vòng, lấy mẫu lại theo công ty, seed 42.

Ban đầu ngưỡng theo nhóm cũng được so bằng cận bootstrap. Khi chạy trên dữ liệu thật, nhóm chỉ có 26–126 tin test nên khoảng bootstrap quá rộng: 9/12 vai trò được chấm và 5/7 cấp bậc trượt, kể cả Backend và Junior dù giá trị điểm của hai nhóm này đạt. Người dùng chọn so ngưỡng nhóm bằng giá trị điểm; khoảng tin cậy của nhóm vẫn được lưu để tham khảo (ghi ở #87). Ngưỡng chung vẫn so bằng cận bất lợi.

Nhóm dưới 20 tin test không được chấm và không tính là trượt. Mọi ngưỡng được khai báo ở một chỗ trong code.

**Khi nào hiện con số lương.** Một hồ sơ chỉ hiện con số khi thỏa cả hai điều kiện:
- thuộc **Nhóm đủ dữ liệu** (vai trò × cấp bậc có ≥ 20 tin train);
- cả vai trò lẫn cấp bậc của nó không trượt ngưỡng nhóm.

Hồ sơ không thỏa chỉ nhận khoảng lương mở rộng, kèm cảnh báo ít dữ liệu và lý do; không có con số và không có thứ hạng phân vị trong vai trò. Khoảng mở rộng của mỗi vai trò và mỗi cấp bậc là p10/p90 của tỉ lệ lương thật / lương dự đoán trên tập valid. Nếu nhóm có dưới 20 tin valid thì dùng p10–p90 lương thị trường trên tập train. Hồ sơ bị chặn lấy khoảng rộng hơn trong khoảng của vai trò và của cấp bậc. Tập test chỉ dùng để chấm.

**Cổng thay model khi huấn luyện lại.** Huấn luyện lại ghi vào thư mục ứng viên rồi chạy kiểm định. Ứng viên chỉ thay model đang phục vụ khi:
- ứng viên đạt chuẩn production; hoặc
- model đang phục vụ chưa đạt, và ứng viên không tệ hơn ở chỉ số chung nào (độ phủ được so theo khoảng cách tới 80%) và qua được nhiều phạm vi hơn.

Trường hợp còn lại giữ model cũ, báo lý do và giữ ứng viên để phân tích. Quy tắc chọn mô hình theo valid MAE không đổi.

## Hiện trạng

Model Gradient Boosting đang phục vụ chưa đạt chuẩn production:

| Chỉ số chung | Giá trị điểm | Khoảng 95% | Ngưỡng |
|---|---|---|---|
| Trung vị sai số | 16.5% | [15.4, 18.0] | ≤ 15% |
| Tỉ lệ sai ≤ 20% | 59.1% | [54.4, 63.0] | ≥ 65% |
| Độ phủ p10–p90 | 77.9% | [74.4, 80.2] | 75–85% |

Các nhóm trượt là vai trò Bảo mật, Quản lý dự án / sản phẩm và cấp bậc Lead, Manager.

Trên tập test, 67% số tin thuộc hồ sơ được hiện con số. Khoảng p10–p90 phủ đúng 80.6% ở nhóm đủ dữ liệu, khoảng mở rộng phủ đúng 87.7% ở phần còn lại.

Theo #77, nhiễu nhãn lương chỉ chiếm khoảng 2tr MAE. Với đặc trưng hiện có, mức sai thấp nhất đạt được khoảng 4–5.5tr MAE, nên muốn đạt chuẩn cần thông tin mới (#81). Ứng dụng ghi rõ cho người dùng rằng model chưa đạt chuẩn và kết quả chỉ mang tính tham khảo.

## Quan hệ với ADR trước

**ADR 0008 — không trả lương khi không đủ mẫu hỗ trợ.** ADR 0008 nói không trả lương hay tư vấn khi hồ sơ không đủ mẫu hỗ trợ. Quyết định này đổi thành: không trả **con số**, nhưng vẫn trả khoảng mở rộng và tư vấn kỹ năng. Lý do là khoảng mở rộng vẫn phủ đúng khoảng 88% trên test, hữu ích hơn việc không trả gì. Ngưỡng hỗ trợ mà ADR 0008 để mở nay được khóa ở 20 tin train.

**ADR 0008 — không promote khi test không đạt, không lặp thử trên test.** ADR 0008 cũng nói không promote khi test không đạt và không lặp thử nhiều cấu hình trên cùng test. Nhánh thứ hai của cổng thay model (cả hai chưa đạt, ứng viên tốt hơn) có so hai lần huấn luyện trên test. Nhánh này được giữ có chủ đích, để các cải tiến dần dần như #81 lên được production trước khi đạt chuẩn. Cổng không chọn siêu tham số hay mô hình theo test; việc đó vẫn chỉ dựa trên valid. Rủi ro còn lại: nếu lặp lại nhiều lần huấn luyện chỉ để vượt cổng, tập test sẽ dần bị "dùng" để chọn. Nên khi có dữ liệu mới, cần làm mới tập test.

**ADR 0009 — số gợi ý kỹ năng.** Lệch về số gợi ý kỹ năng, đã ghi ở ADR 0013, không thay đổi ở đây.
