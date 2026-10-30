# Nhãn đã khóa trước fit

Nguồn mới: Việt Thành Nguyễn, vitthnhnguyn138/vietnam-it-job-posts v1 trên Kaggle, khai báo MIT. Raw đủ 6.779 dòng nằm ở datasets/raw/vietnam_it_job_posts_v1.csv; metadata và README publisher nằm ở datasets/provenance/training-2026-10-30. Raw không bị sửa.

Đây là bộ nhãn do agent kiểm duyệt theo ủy quyền trực tiếp của người dùng, không phải nhãn được publisher/chuyên gia chứng nhận. 14 entity/11 công ty có tiêu đề nghề rõ và khoảng VND/tháng. Tất cả giữ unknown gross/net, salary_components_unspecified. Không trộn thu nhập tháng YODY hoặc USD, không dùng skills/field/job_hash của publisher để học. Kinh nghiệm số chưa rõ đơn vị giữ raw, không tự coi là năm.

accepted.json/csv là snapshot trước fit; review-ledger.json lưu quyết định sàng lọc của 336 dòng có khoảng VND/tháng đúng grammar. Không khẳng định đã gán nghề thủ công cho toàn bộ 6.779 dòng. readiness-before-fit.json lưu nhãn và membership preview trước fit; manifest ghi SHA-256 từng file và policy. README này được thêm sau fit nên nằm ngoài manifest dữ liệu đã khóa.

Không sửa các file đã khóa để tạo run mới trên test đã xem. Corrections về dòng 779/2243 và kỹ năng Go ở 5831 được lưu riêng trong provenance/training-2026-10-30/post-fit-corrections.json. Bộ trích hiện tại đã sửa, model lịch sử giữ nguyên; lần sửa model tiếp theo cần holdout chưa dùng.
