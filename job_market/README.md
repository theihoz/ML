# Phân tích thị trường việc làm CNTT Việt Nam

Ứng dụng mới viết bằng Python và Streamlit, chạy trực tiếp trên máy. Đã có nhập liệu, chuẩn hóa, kiểm tra chất lượng, EDA, preview hồ sơ CSV/Excel và xem trước chia tập theo công ty.

Đã tự huấn luyện Ridge và Linear Regression từ đầu trên cohort thăm dò mới: 14 nhãn/11 công ty, chia theo công ty 10 train / 2 validation / 2 test. Ridge được chọn bằng validation MAE; test MAE 21,98 triệu VND/tháng, RMSE 22,20 triệu, baseline MAE 32,50 triệu. Mẫu quá nhỏ và chưa có kinh nghiệm theo năm được xác minh; chưa mở suy luận/tư vấn theo hồ sơ. Xem trang Kết quả huấn luyện để đối chiếu model, metric, membership và nạp lại artifact.

## Chạy ứng dụng

Từ thư mục repository:

```sh
cd job_market
python3.11 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
make check PYTHON=.venv/bin/python
make run PYTHON=.venv/bin/python
```

Mở http://127.0.0.1:8502. Có thể đổi cổng bằng `PORT=8503` khi gọi make run. Môi trường .venv riêng nằm trong job_market.

## Các màn hình

- Trang chính: top kỹ năng theo nguồn, nghề, địa điểm và Remote; bảng/biểu đồ cùng số mẫu, tải CSV/PNG.
- Nguồn dữ liệu và Tải nguồn: raw, xuất xứ, revision, giấy phép và checksum; tải lại đúng phiên bản.
- Vai trò, Địa điểm, Kỹ năng, Lương, Kinh nghiệm: đối chiếu raw–chuẩn, bằng chứng, trạng thái cần rà soát và CSV.
- Chất lượng: đối chiếu các partition, nhóm trùng/cùng trường quan sát và tải snapshot kèm manifest.
- Độ phủ thời gian: giữ riêng nguồn/tháng đăng, giải thích khi chưa đủ cơ sở kết luận xu hướng.
- Preview CSV: ghép cột hồ sơ, giữ thứ tự và lỗi từng dòng; UTF-8, tối đa 5 MiB/10.000 dòng.
- Preview Excel: chọn sheet và ghép cột trước chuẩn hóa; từ chối công thức/macro, không huấn luyện khi upload.
- Đối chiếu công ty: alias bảo thủ, nhóm liên thông công ty/trùng/đăng lại và các danh tính cần review.
- Train / validation / test: xem trước mục tiêu 70/15/15, seed 42, số mẫu và tỷ lệ thực; chưa xuất manifest huấn luyện khi gate/policy chưa được duyệt.
- Kết quả huấn luyện: đọc run đã lưu, so Ridge/Linear Regression/baseline bằng MAE và RMSE, kiểm nạp lại model. Trang không có nút fit.

## Dữ liệu mới

Hai nguồn được tải mới đúng revision, raw giữ nguyên tại datasets/raw. Metadata/attribution nằm trong datasets/provenance, datasets/README.md và src/career_market/sources.json.

| Nguồn | Phiên bản | Dòng thô | Khai báo giấy phép |
| --- | --- | ---: | --- |
| lucaznguyenofficial/vietnamese-job-posting-vietnamese-version | 2 | 2.056 | CC0 |
| baocgb/vietnam-it-jobs-raw-data-from-topcv-2026 | 1 | 1.550 | CC BY 4.0 |

Sau quy tắc nghề hiện tại: 320 tin EDA, 556 tin cần rà soát vai trò và 2.730 tin ngoài bảy nhóm nghề. Đây là phạm vi quan sát của dataset; các quy tắc bảo thủ có thể bỏ sót tin. TopCV thiếu JD nên kỹ năng chỉ có chứng cứ từ tiêu đề. Hai nguồn khác nền tảng và thời gian, chưa đủ cơ sở so sánh xu hướng nhiều năm.

HCM/HN giữ chung alias, Remote là hình thức làm việc riêng. Lương giữ khoảng/cận/tiền tệ/kỳ; chỉ có target khi đủ chứng cứ VND/tháng. Tin thiếu lương vẫn có thể dùng cho EDA. Ledger hai nguồn EDA bổ sung **2 nhãn thu nhập tháng của cùng YODY**, gross/net chưa rõ, giữ riêng phạm vi thu nhập. Cohort YODY chỉ có một nhóm công ty nên vẫn chưa thể chia ba tập độc lập hoặc huấn luyện. Báo cáo cột lương raw riêng vẫn không có target khi thiếu bằng chứng kỳ trả.

Đoạn trên mô tả riêng hai nguồn EDA và cohort YODY. Run ML mới dùng nguồn thứ ba độc lập: vitthnhnguyn138/vietnam-it-job-posts v1, raw 6.779 dòng, publisher khai báo MIT. Chỉ nhận 14 entity có bằng chứng VND/tháng và nghề rõ trong tiêu đề, giữ salary_components_unspecified/unknown riêng; không trộn YODY, USD hay dữ liệu cũ. Policy và nhãn đã khóa nằm ở config/training-policy-v1.json và datasets/labels/2026-10-30. Model/metric mới của cohort này có trong artifacts/runs/7137291a5d16b71f1861.

## Lệnh dữ liệu

Chạy từ job_market:

```sh
PYTHONPATH=src .venv/bin/python -m career_market sources
PYTHONPATH=src .venv/bin/python -m career_market preview jobs-2026 --limit 5
PYTHONPATH=src .venv/bin/python -m career_market download jobs-2026
PYTHONPATH=src .venv/bin/python -m career_market prepare --output datasets/processed
PYTHONPATH=src .venv/bin/python -m career_market split-preview --basis unknown --scope advertised_monthly_income --output /tmp/split-preview.json
PYTHONPATH=src .venv/bin/python -m career_market training-readiness
PYTHONPATH=src .venv/bin/python -m career_market train
PYTHONPATH=src .venv/bin/python -m career_market training-report
```

Snapshot gồm rows, eda, review, duplicates, salary_targets, nhóm cùng trường quan sát và manifest SHA-256. Tập target rỗng vẫn có schema. Thư mục processed và cache archives được sinh lại bằng lệnh, không thay raw.

CLI và Streamlit cùng gọi MarketService. Kiểm tra lint, nghiệp vụ và smoke UI/CLI bằng make check; bằng chứng từng lát cắt nằm trong docs/tdd. Workflow chỉ kiểm tra ứng dụng mới này.

Lệnh train trả lại run đã có nếu cohort đã được đánh giá; không fit/test lại chỉ vì gọi lại lệnh hoặc đổi thư mục output. Snapshot nhãn/membership trước fit và report/model đã lưu được kiểm SHA-256. Kỹ năng Go bị bỏ sót trong run đầu đã được ghi vào addendum; bộ trích hiện tại đã sửa nhưng không thay metric/model lịch sử bằng một lần thử lại trên test đã xem.
