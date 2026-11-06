# Thuật ngữ

Giải thích bằng lời thường, xếp theo nhóm. Định nghĩa chuẩn của các thuật ngữ nghiệp vụ nằm ở [`GLOSSARY.md`](../../GLOSSARY.md); ký hiệu 📘 nghĩa là thuật ngữ đó có trong GLOSSARY.

## Về lương

| Thuật ngữ | Nghĩa | Ví dụ |
|---|---|---|
| **Lương chào tuyển** 📘 | Mức lương ghi trong tin tuyển dụng; chưa rõ là gross hay net | "15 – 25 triệu" |
| **Lương thị trường (gross)** 📘 | Lương trước thuế, bảo hiểm mà người đang làm vị trí đó nhận, theo khảo sát lương công bố | Trung vị Backend của TopDev: 33,5 triệu |
| **Gross / net** | Gross là trước khi trừ thuế và bảo hiểm; net là số tiền thực nhận | Gross 20 triệu ≈ net 17–18 triệu |
| **Lương trung điểm** 📘 | Điểm giữa của khoảng lương trong tin; là con số mô hình học | "15 – 25 triệu" → 20 triệu |
| **Tin chỉ ghi một con số** | Tin chỉ ghi "Tới X" hoặc "Từ X"; đầu còn lại phải đoán | "Tới 30 triệu" |
| **Khoảng lương dự đoán** 📘 | Kết quả chính của app: p25 – trung vị – p75 khi đủ dữ liệu; khoảng rộng hơn khi ít dữ liệu | 13,4 – 16,3 – 19,3 triệu |
| **Mức điển hình** | Trung vị của khoảng lương dự đoán | 16,3 triệu |
| **Hiệu chỉnh gross** | Nhân dự đoán lương chào tuyển với một hệ số để quy về lương thị trường gross gần đúng | × 1,22 cho Backend Junior ở Hà Nội |

## Về thống kê

| Thuật ngữ | Nghĩa | Ví dụ |
|---|---|---|
| **Trung bình** | Cộng tất cả rồi chia số lượng; dễ bị kéo lệch bởi vài giá trị rất lớn | 9 người 20 triệu + 1 người 200 triệu → 38 triệu |
| **Trung vị** | Giá trị đứng giữa khi xếp từ thấp đến cao; mô tả "người bình thường" | Ví dụ trên → 20 triệu |
| **Phân vị (P…)** | P25 là mức mà 25% số giá trị thấp hơn; P75 là mức mà 75% thấp hơn | P90 lương là mức chỉ 10% tin cao hơn |
| **Vị trí so với vai trò** | Phân vị của mức lương dự đoán trong các tin cùng vai trò. App ghi "Cao hơn 14% tin" thay cho "P14" | Backend Junior Hà Nội (Java, SQL): P14 = cao hơn 14% tin, thấp hơn 86% tin |
| **Tương quan** | Hai thứ hay đi cùng nhau; **không** có nghĩa cái này gây ra cái kia | Tin đòi AWS thường lương cao, nhưng có thể vì tin đó tuyển Senior |
| **Hệ số Spearman** | Mức độ hai đại lượng cùng tăng theo thứ tự (−1 đến 1) | Kinh nghiệm và lương: khoảng 0,7 |
| **Khoảng tin cậy 95%** | Khoảng mà giá trị thật nằm trong đó với độ chắc chắn 95% | Sai số MAE: 5,6 – 7,7 triệu |
| **Bootstrap** | Bốc ngẫu nhiên lại dữ liệu (có thể trùng) nhiều lần để xem kết quả dao động bao nhiêu | "Thi lại 1.000 lần với đề khác" |

## Về học máy

| Thuật ngữ | Nghĩa | Ví dụ |
|---|---|---|
| **Mô hình** | Một công thức máy tự tìm ra từ dữ liệu để đoán lương từ hồ sơ | Gradient Boosting |
| **Đặc trưng** | Thông tin đầu vào mô hình được xem | Vai trò, khu vực, số năm kinh nghiệm, kỹ năng |
| **Nhãn** | Đáp án mô hình học để đoán | Lương trung điểm của tin |
| **Tập học (train)** | Phần dữ liệu mô hình được xem để học (≈ 70%) | 1.169 tin |
| **Tập chọn (valid)** | Phần dùng để so và chọn mô hình, thiết lập (≈ 15%) | 278 tin |
| **Tập kiểm tra (test)** | Phần chỉ mở một lần ở cuối để chấm điểm thật (≈ 15%) | 288 tin |
| **Chia theo công ty** | Mỗi công ty nằm trọn trong một tập, để kiểm tra đúng trên công ty chưa từng gặp | — |
| **Học thuộc (overfit)** | Mô hình nhớ ví dụ đã thấy thay vì hiểu quy luật; tốt trên tập học, kém trên tập kiểm tra | Sai 5,5 triệu trên train, 6,6 triệu trên valid |
| **Siêu tham số** | Thiết lập của mô hình do người chọn, không tự học | Tốc độ học, số lá tối đa |
| **Mốc trung vị (Baseline)** | "Mô hình" luôn trả lời trung vị chung; mức tối thiểu phải vượt | Sai 11,3 triệu |
| **Ridge** | Mô hình cộng điểm: mỗi đặc trưng cộng/trừ một lượng cố định | Backend +2, mỗi năm +3 |
| **Random Forest** | Trung bình của 300 cây quyết định, mỗi cây xem một phần dữ liệu | — |
| **Gradient Boosting** | Chuỗi cây, cây sau sửa lỗi của cây trước; mô hình được chọn | — |
| **Ràng buộc đơn điệu** | Quy tắc buộc mô hình: thêm kỹ năng hoặc kinh nghiệm thì lương dự đoán không giảm | ADR 0013 |
| **Permutation importance** | Xáo trộn một đặc trưng rồi xem mô hình kém đi bao nhiêu để biết đặc trưng đó quan trọng thế nào | Kinh nghiệm quan trọng nhất |
| **Mức tăng lương của kỹ năng** | Lương dự đoán khi thêm đúng một kỹ năng trừ lương hiện tại, giữ nguyên mọi thứ khác | + 5,7 triệu khi thêm Kafka |

## Về đánh giá

| Thuật ngữ | Nghĩa | Ví dụ |
|---|---|---|
| **MAE** | Trung bình mô hình đoán lệch bao nhiêu triệu mỗi tin | 6,49 triệu |
| **RMSE** | Giống MAE nhưng phạt nặng các lần lệch lớn | — |
| **R²** | Mô hình giải thích được bao nhiêu phần sự khác nhau giữa các mức lương (0 đến 1) | 0,62 |
| **MAPE** | Trung bình lệch bao nhiêu phần trăm | 23% |
| **Hiệu chuẩn khoảng** | Khoảng "80%" có thật sự chứa lương thật khoảng 80% số lần không | Đúng 83% |
| **Độ lệch công bằng** | Mô hình đoán cao/thấp đều cho một nhóm nào đó bao nhiêu % | Junior bị đoán cao ~7% |
| **Chuẩn production** | Mức chất lượng tối thiểu để đưa cho người dùng thật, theo cách Glassdoor/LinkedIn công bố | ADR 0014 |
| **Bộ đối chiếu** 📘 | Số liệu lương từ báo cáo bên ngoài dùng để kiểm tra độ chính xác thực tế, không dùng để học | TopDev 2024–2025 |
| **Nhóm đủ dữ liệu** 📘 | Vai trò × cấp bậc có ít nhất 20 tin để học; chỉ nhóm này được hiện con số | Backend × Junior |

## Về dữ liệu và vận hành

| Thuật ngữ | Nghĩa |
|---|---|
| **Tin sinh tự động** 📘 | Tin giả do bộ dữ liệu sinh ra (đường dẫn chứa `-hist`); đã loại 2.400 tin |
| **Gán nhãn tự động** | Quy tắc tự đọc lương, vai trò, cấp bậc, kỹ năng từ chữ trong tin |
| **Hàng đợi duyệt tay** | Tin mới mà máy không gán nhãn được, chờ người xem |
| **Sổ nhãn đã duyệt** | File ghi quyết định của người duyệt; áp dụng ở lần tạo dữ liệu sau |
| **Lô (batch)** | Một file CSV tin tuyển dụng mới được nhập vào |
| **Phiên bản model** | Mỗi lần huấn luyện lại tạo một thư mục riêng; có thể quay lại bản cũ |
| **Cổng thay model** | Mô hình mới chỉ được dùng khi đạt chuẩn hoặc tốt hơn mô hình cũ |
| **Dòng độ mới** | Dòng trên app cho biết phiên bản, ngày cập nhật, số tin học, trạng thái chuẩn |
| **Vùng ưu tiên** 📘 | Hà Nội, TP. Hồ Chí Minh và tám vai trò phổ biến; ngoài vùng này app cảnh báo ít dữ liệu |
