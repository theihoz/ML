# Bộ đối chiếu

`salary_reference.csv` stores million VND/month. It is excluded from model fitting.

- `evaluation`: all ten national TopDev 2024–2025 gross role medians, pages 28–30. Grouped roles use published occupational representatives as disclosed in each row. These are not city/level cells.
- `calibration`: fifteen TopDev level/city gross **means**, page 25, separate approximate anchors for later calibration. Lead and Manager share one source cell.
- `role_calibration`: ten fixed occupational representatives per verified ITviec edition (2023–2024 and 2024–2025), for #117. Equal edition weight produces an approximate composite anchor, not a pooled population median. Tester represents QA/QC; DevOps/DevSecOps represents DevOps/Cloud. Data Analyst includes DS and AI includes Blockchain: imperfect proxies disclosed in `mapping_caveat`. Alternative Cloud and QA-QC rows remain `context`.
- `context` with unknown basis: ITviec 2025–2026 public role/experience figures, excluded from gross scoring. Earlier editions' verified gross basis does not establish the 2025–2026 basis.

`value` means exactly `statistic`; `median` is populated only for median rows. Blank p25/p75 means unpublished, not inferred from a salary range. Blank `sample_size` means unknown cell count; `report_total_respondents` is a separate report total. ITviec experience coordinates are median years **in the current position**, not total experience and not a restriction on the national role cohort.

TopDev values retain the known PDF mirror URL, explicitly distinguished from the publisher landing page in notes. ITviec verified rows link to primary official PDFs with printed and PDF page numbers. Full methodology and sources: `docs/research/luong-it-viet-nam-doi-chieu.md`.

TopDev USD values multiply by the report's stated 25,000 VND/USD, then divide by 1,000,000. VND values divide by 1,000,000. No net figures are converted: a future conversion needs an explicit sourced tax/insurance rule; unknown is never silently gross.

`python -m career_market reality-check` scores saved predictions at inference year 2026 on TRAIN profiles, without reading their salaries as survey outcomes. It reports all ten evaluation cells, counts missing cohorts against the denominator, and applies ≤15% error in ≥80% of cells. Means and unknown-basis figures appear separately. This initial report precedes market calibration and may fail; no inflation adjustment or HN/HCM subgroup accuracy is claimed.


## Hồ sơ vàng

`golden_profiles.csv` là mẫu chỉ có tiêu đề, không chứa hồ sơ giả hoặc dữ liệu cá nhân.
Chỉ thêm các cột mẫu; không ghi tên, email, số điện thoại hoặc công ty. Sao chép file
để giữ dữ liệu riêng; chạy `python -m career_market reality-check --golden-path /path/to/private.csv`.
Trang Đánh giá đọc file mặc định; sau khi cập nhật file hãy khởi động lại ứng dụng.
File nằm cùng thư mục reference đã được đóng gói trong wheel và Docker.

| Cột | Cách điền |
| --- | --- |
| `role` | Một vai trò chuẩn trong danh sách bên dưới. |
| `level` | Một cấp bậc chuẩn; nhập trực tiếp, không suy từ số năm. |
| `region` | Một nhãn khu vực chuẩn, không dùng HN/HCM viết tắt. |
| `experience_years` | Tổng năm kinh nghiệm, số hữu hạn 0–60; có thể là số thập phân. |
| `skills` | Tên kỹ năng chuẩn, phân tách bằng dấu `|` (ví dụ `Java|SQL`); để trống nếu không có. |
| `gross_salary` | Lương gross hàng tháng, **triệu VND/tháng**, dương và hữu hạn; 22 nghĩa là 22 triệu. Không nhập VND nguyên, USD, net, thưởng hoặc tổng thu nhập năm. |
| `year` | Năm ghi nhận lương, số nguyên 2023–2026. |

Dùng đúng nhãn, phân biệt hoa/thường. Giá trị không hợp lệ báo lỗi với số dòng và tên cột,
không âm thầm bỏ qua hồ sơ. Quy tắc hiện tại dự đoán ở năm 2026 như form tư vấn;
`year` giữ năm ghi nhận để truy xuất, **chưa điều chỉnh lạm phát hoặc quy đổi thời giá**.
Không tuyên bố kết quả là dự đoán lịch sử của năm ghi nhận.

Mỗi hồ sơ đạt khi `|trung vị dự đoán − gross_salary| / gross_salary ≤ 20%`.
Bộ hồ sơ đạt khi ≥70% hồ sơ đạt. Mẫu chỉ có tiêu đề trả `status: "chưa có dữ liệu"`,
`passed: null`, `total: 0`; không tính là trượt. Kết quả trả trung vị, độ lệch tương đối
và kết luận từng dòng, đồng thời xuất hiện trong CLI và trang Đánh giá.
Hồ sơ vàng chỉ được đọc khi chấm đối chiếu; bộ dựng dữ liệu chỉ đọc ba nguồn tin ở
`datasets/raw`, và huấn luyện chỉ fit phần train của bộ dữ liệu đã dựng.

Vai trò (`role`, `ROLE_ORDER`): `Quản lý IT / CTO`, `Tech Lead / Architect`, `Bảo mật`, `AI / ML Engineer`, `Data Engineer`, `Data Analyst / BI`, `Quản trị CSDL (DBA)`, `DevOps / Cloud`, `Kiểm thử (QA/QC)`, `BrSE / Cầu nối`, `Business Analyst`, `Quản lý dự án / sản phẩm`, `UI/UX Designer`, `Game Developer`, `Embedded / IoT`, `Mobile Developer`, `Fullstack Developer`, `Frontend Developer`, `ERP / SAP Consultant`, `Backend Developer`, `Quản trị hệ thống / Mạng`, `IT Support / Helpdesk`, `Software Engineer (chung)`.

Cấp bậc (`level`, `LEVELS`): `Intern`, `Fresher`, `Junior`, `Middle`, `Senior`, `Lead`, `Manager`.

Khu vực (`region`, `REGIONS`): `Hà Nội`, `TP. Hồ Chí Minh`, `Đà Nẵng`, `Tỉnh/thành khác`, `Remote`.

Kỹ năng (`skills`, `SKILLS`): `Python`, `Java`, `JavaScript`, `TypeScript`, `C#`, `C++`, `PHP`, `Golang`, `Kotlin`, `Swift`, `Dart`, `Ruby`, `Rust`, `Scala`, `SQL`, `HTML/CSS`, `React`, `React Native`, `Vue.js`, `Angular`, `Node.js`, `Next.js`, `.NET`, `Spring Boot`, `Django`, `FastAPI/Flask`, `Laravel`, `Flutter`, `Unity`, `MySQL`, `PostgreSQL`, `MongoDB`, `Redis`, `SQL Server`, `Oracle`, `AWS`, `Azure`, `GCP`, `Docker`, `Kubernetes`, `Linux`, `Git`, `CI/CD`, `Microservices`, `REST API`, `Kafka`, `Spark`, `Airflow`, `Power BI`, `Tableau`, `Excel`, `Machine Learning`, `Deep Learning`, `TensorFlow/PyTorch`, `NLP`, `Computer Vision`, `LLM / GenAI`, `Selenium`, `Automation Test`, `Figma`, `Agile/Scrum`, `Jira`, `SAP`, `Odoo`, `Mạng (CCNA)`, `An ninh mạng`, `Embedded C`, `Tiếng Anh`, `Tiếng Nhật`.

Các từ vựng dùng chung với form tại `src/career_market/data/rules.py`.
