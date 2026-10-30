# Run huấn luyện thực tế 30/10/2026

Ủy quyền mới của người dùng cho phép agent tự kiểm duyệt nhãn, chốt policy và huấn luyện. ADR0010 ghi phạm vi và lựa chọn trước fit. Không dùng dữ liệu/model cũ của người dùng, model pretrained hoặc field kỹ năng/vai trò được publisher suy diễn.

Nguồn mới vitthnhnguyn138/vietnam-it-job-posts v1: 6.779 dòng, SHA-256 d201d539d1bbc79a54a369eafc94d85efbb10bdece9f6ac80b9e5e4c9a0bc30c; MIT theo metadata publisher. 336 dòng có grammar khoảng VND/tháng được lưu ledger; nhận 14 entity/11 công ty từ tiêu đề nghề rõ, cùng unknown basis/salary_components_unspecified. Thu nhập YODY, tin thỏa thuận/một cận, USD, recruiter chưa rõ và phiên bản mâu thuẫn không được trộn vào run. Tiêu đề không phải bằng chứng đầy đủ của kỹ năng trong JD.

Policy SHA-256: 33cadf3ac969766f3eec7cb9503ae04613c1f1688f352c44ec0fd044cec7ce86. Manifest nhãn trước fit: 4bb9edadeaf88122a038309fe10c781d4be66800a60623b29457396a08116cab. Tỷ lệ mục tiêu 70/15/15, seed42, thực tế 10/2/2 tin và 7/2/2 nhóm công ty; không có công ty/nhóm giao tập. Giữ outlier hợp lệ, không chỉnh seed/alpha sau khi nhìn test. Ridge alpha10/SVD và OLS khởi tạo mới, cùng preprocessing/vocabulary/scaler chỉ fit train. Target được đổi về triệu trong fit, dự đoán/metric lưu VND/tháng.

| Model | Validation MAE | Validation RMSE | Test MAE | Test RMSE |
| --- | ---: | ---: | ---: | ---: |
| Ridge | 10,50 | 11,62 | 21,98 | 22,20 |
| Linear Regression | 13,58 | 13,72 | 17,58 | 17,66 |
| Trung vị train | 11,25 | 11,86 | 32,50 | 42,57 |

Đơn vị bảng: triệu VND/tháng; validation/test mỗi tập n=2. Các số chưa làm tròn nằm trong report.json. Ridge được chọn bằng validation trước khi xem test; không chuyển sang OLS dù test OLS tốt hơn. Ridge thắng baseline trên cả validation/test nên đạt tiêu chí baseline đã chốt. Điều đó không chứng minh độ chính xác đủ tốt cho nghề/thị trường hoặc hồ sơ bất kỳ.

Run: 7137291a5d16b71f1861. Report SHA-256 5ffa9e899695b58ed9aca2b07b334276c11479c642e9b7377981adaaca0c6d5e. Thư mục job_market/artifacts/runs/7137291a5d16b71f1861 chứa hai pipeline joblib, policy, split, selection, predictions, train-support và report. Nạp lại trong tiến trình mới cho sai lệch tối đa 0 VND trên 10 hồ sơ train đối chiếu; không fit lại. Wheel cũng đã được build/extract ở thư mục độc lập, xác nhận đọc nhãn/policy và nạp lại cùng model, không phụ thuộc cwd source.

Giới hạn: 0/14 entity có số năm kinh nghiệm đủ chứng cứ; chỉ 3 tin có kỹ năng trích từ tiêu đề; train có nghề chỉ 1–2 mẫu và không có Fullstack. Không mở tư vấn/suy luận theo hồ sơ thiếu hỗ trợ, không bịa delta kỹ năng. Chưa hoàn tất ML11–ML23 chỉ vì đã có hai model.

Review độc lập tìm thấy Go bị bỏ sót trong danh sách có ngoặc ở dòng 5831 và lineage repost 779/2243 chưa đủ. Parser/lineage hiện tại đã sửa, nhưng snapshot/metric/model đầu tiên được giữ nguyên. Addendum ở datasets/provenance/training-2026-10-30/post-fit-corrections.json ghi rõ; không tự fit lại correction trên test đã xem.

Guard sau review: tải snapshot nhãn/membership đã khóa, từ chối checksum/rules drift; reservation theo nguồn/cohort/entity độc lập thư mục output, giữ cả khi run ngắt; artifact phải đủ file, đúng model allowlist/hash/path và approved report trước deserialize. Thao tác nạp chỉ dành cho artifact dự án đã tạo, không có đường upload pickle từ người dùng.

Đã kiểm tra 313 test đạt, Ruff lint/format và diff check đạt; trang /Huan_luyen hiển thị Ridge, 21,98 triệu test MAE, nạp lại khớp, không exception. Các kiểm thử bổ sung sau review kiểm guard đổi output root, manifest thiếu/path traversal và giao diện. Chưa push trong đợt này.
