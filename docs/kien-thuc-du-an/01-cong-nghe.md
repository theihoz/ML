# Công nghệ sử dụng

Phiên bản lấy từ `job_market/pyproject.toml` và `Dockerfile`.

| Công cụ | Phiên bản | Dùng để làm gì | Vì sao chọn |
|---|---|---|---|
| **Python** | 3.11 | Ngôn ngữ của toàn bộ dự án | Đề tài môn Lập trình Python; hệ sinh thái phân tích dữ liệu mạnh nhất |
| **pandas** | 3.1.0 | Đọc file CSV, lọc, gộp, đếm, tính trung vị | Làm việc với bảng dữ liệu như Excel nhưng bằng code, chạy lại được |
| **NumPy** | 2.4.6 | Tính toán số học trên mảng (phân vị, logarit) | Nền tảng của pandas và scikit-learn |
| **scikit-learn** | 1.9.1 | Các mô hình Ridge, Random Forest, Gradient Boosting; tiền xử lý; chỉ số MAE, R² | Thư viện học máy chuẩn, có sẵn ràng buộc đơn điệu cho Gradient Boosting |
| **SciPy** | 1.17.1 | Giải bài toán Ridge có chặn hệ số kỹ năng ≥ 0 (`lsq_linear`) | Cần thiết để Ridge tuân theo "thêm kỹ năng không giảm lương" |
| **joblib** | 1.6.0 | Lưu và nạp mô hình đã huấn luyện (`.joblib`) | Định dạng mặc định của scikit-learn, nạp nhanh |
| **Matplotlib** | 3.11.2 | Vẽ mọi biểu đồ (web, notebook, báo cáo) | Vẽ một lần, dùng chung cho ba nơi |
| **seaborn** | 0.13.2 | Biểu đồ hộp, bản đồ nhiệt, biểu đồ cột đẹp hơn | Viết ít code hơn Matplotlib thuần |
| **Streamlit** | 1.66.1 | Giao diện web 5 trang | Viết web bằng Python thuần, không cần HTML/JavaScript |
| **Jupyter** (nbformat, nbclient) | – | 7 notebook trình bày từng bước | Vừa chạy code vừa viết giải thích; CI chạy thử để notebook không hỏng |
| **pytest** | 9.2.0 | Kiểm thử tự động (230 test) | Bảo đảm sửa chỗ này không làm hỏng chỗ khác |
| **Ruff** | 0.17.3 | Kiểm tra và định dạng code | Nhanh, một công cụ thay cho nhiều công cụ |
| **Docker / Docker Compose** | python:3.11-slim | Đóng gói app cùng dữ liệu và mô hình để demo không cần mạng | Chạy giống nhau trên mọi máy |
| **GitHub Actions** | – | Tự chạy lint + test mỗi lần đẩy code | Phát hiện lỗi trước khi gộp |
| **Node.js** (pptxgenjs, docx) | – | Sinh slide `.pptx` và kịch bản `.docx` từ một file nội dung | Sửa số liệu một chỗ, slide và kịch bản cùng cập nhật |

## Ba bộ dữ liệu

| File | Nguồn | Giấy phép |
|---|---|---|
| `raw/topcv_jobs.csv` | *Vietnam IT Jobs – Raw Data from TopCV (2026)*, Kaggle | CC BY 4.0 |
| `raw/vietnam_it_job_posts_v1.csv` | *ADY201m Dataset* (VietnamWorks, ITviec, TopCV, CareerViet), Kaggle | MIT |
| `raw/vietnamese-job-posting.csv` | *Vietnamese Job Posting* (CareerBuilder 2023), Kaggle | CC0 |

Chi tiết: `job_market/datasets/README.md`. Báo cáo lương dùng để đối chiếu (TopDev, ITviec, Adecco): `docs/research/luong-it-viet-nam-doi-chieu.md`.

## Không dùng gì, và vì sao

- **Không dùng mạng nơ-ron / LLM để dự đoán lương:** dữ liệu chỉ có 1.735 tin; mô hình cây và tuyến tính đủ tốt, giải thích được và chạy nhanh.
- **Không có cơ sở dữ liệu hay API riêng:** mô hình nạp thẳng trong Python; demo chỉ cần một container.
- **Không tự crawl trang tuyển dụng:** đang chờ xác nhận điều khoản thu thập của từng trang (#103).
