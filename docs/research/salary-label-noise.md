# Độ nhiễu của nhãn lương và sàn sai số đạt được

Ngày kiểm tra: 06/11/2026. Trả lời issue [theihoz/ML#77](https://github.com/theihoz/ML/issues/77) (map #76). Ghi chú nghiên cứu, không phải quyết định đã duyệt.

Cơ sở: nhánh `dev/ml-development` @ `9f7afad`; dữ liệu `job_market/datasets/processed/salary_dataset_v2.csv` (3 809 tin; train 2 461 / valid 652 / test 696); dự đoán test của mô hình được chọn (Gradient Boosting) trong `job_market/artifacts/salary-v2/test_predictions.csv`; metric gốc trong `job_market/artifacts/salary-v2/metrics.json` (test MAE 5.821 tr, RMSE 8.580, MAPE 20.73%).

Mọi số liệu bên dưới tái lập bằng script [`salary_label_noise.py`](salary_label_noise.py):

```bash
PYTHONPATH=job_market/src job_market/.venv/bin/python docs/research/salary_label_noise.py
```

## Kết luận ngắn

1. **Nhiễu nhãn do độ rộng khoảng nhỏ so với sai số hiện tại.** Nếu lương thật phân bố đều trong khoảng chào, một mô hình đoán đúng trung điểm vẫn sai trung bình **2.03 tr (MAPE ≈ 7.8%)** trên test so với lương thật. Phương sai nhiễu này (width²/12, trung bình 8.3 tr²) chỉ bằng **11%** MSE hiện tại của GB (73.6 tr²).
2. **Nhiễu này không nằm trong con số 5.82 tr.** Metric đang đo so với trung điểm, vốn là hàm xác định của tin, nên độ rộng khoảng không đặt sàn cho MAE-so-với-trung-điểm. Đo so với lương thật (giả định đều), MAE kỳ vọng của GB tăng lên **6.17 tr** và RMSE lên khoảng 9.05.
3. **Phần lớn sai số đến từ việc đặc trưng không phân biệt được các tin.** 31.5% số tin (1 198 tin, 350 nhóm) có vector đặc trưng trùng hệt với tin khác nhưng lương khác. Dự đoán từng tin bằng trung vị của các tin cùng đặc trưng khác (leave-one-out, nhóm ≥ 3) cho **MAE 5.74 tr / MAPE 23.6%**, tức ngang GB (6.06 tr trên phần test thuộc các nhóm này). Với bộ đặc trưng hiện tại, GB đã gần sàn; ước lượng lạc quan nhất (trung vị trong nhóm, in-sample) là 3.84 tr / 15.8%.
4. **Sàn đạt được với đặc trưng hiện tại: khoảng 4–5.5 tr MAE (MAPE 16–20%) so với trung điểm.** Muốn xuống thấp hơn đáng kể cần thêm thông tin (công ty, mô tả chức danh, kỹ năng đầy đủ hơn), không phải mô hình mạnh hơn. Không có cách nào xuống dưới khoảng 2 tr / 7.8% nếu đo so với lương thật, kể cả khi có thông tin hoàn hảo về tin.

## 1. Cách tạo khoảng lương

Phân loại theo nhánh của `parse_salary` (`job_market/src/career_market/salary_dataset.py`, dòng 231–275): hai số → khoảng hai đầu; một số kèm "tới/đến/up to/dưới/max" → `low = 0.7 × high`; một số kèm "từ/trên/from/min" → `high = 1.3 × low`.

| Cách tạo | n | Tỉ lệ |
|---|---:|---:|
| Hai đầu | 3 566 | 93.6% |
| Chỉ ghi đầu trên (low = 0.7x) | 209 | 5.5% |
| Chỉ ghi đầu dưới (high = 1.3x) | 33 | 0.9% |
| Một điểm | 1 | 0.0% |

Tổng tin được suy ra một đầu: **242 tin (6.4%)**.

Phân bố cao/thấp của khoảng hai đầu: trung vị **1.29**, p10 1.16, p25 1.21, p75 1.43, p90 1.67, max 3.0. Theo nhóm: (1, 1.2] 812 tin, (1.2, 1.5] 2 458, (1.5, 2] 426, (2, 2.5] 74, (2.5, 3] 38.

Hệ số suy ra so với thực tế: "từ X" giả định tỉ lệ 1.30, khớp trung vị 1.29 của khoảng hai đầu. "Tới X" giả định tỉ lệ 1/0.7 = 1.43, rộng hơn trung vị. Trên test, GB dự đoán thấp hơn nhãn của tin "tới X" trung bình **−3.28 tr**, so với −1.05 tr ở tin hai đầu. Dấu hiệu này có thể do trung điểm 0.85X bị đặt cao, cũng có thể do "up to" thường là trần thật. Chỉ có 26 tin test nên chưa kết luận được.

## 2. Khác biệt giữa các nguồn

| Nguồn | n | Lương trung vị | Cao/thấp trung vị | Nửa độ rộng / trung điểm | Một đầu | Kỹ năng TB | Thiếu KN |
|---|---:|---:|---:|---:|---:|---:|---:|
| CareerBuilder 2023 | 42 | 24.25 | 1.60 | 0.229 | 7.1% | 3.74 | 7.1% |
| IT Jobs 2026 (careerviet) | 680 | 27.0 | 1.26 | 0.123 | 0% | 3.69 | 0% |
| IT Jobs 2026 (itviec) | 686 | 27.0 | 1.27 | 0.124 | 0% | 3.87 | 0% |
| IT Jobs 2026 (topcv) | 827 | 25.5 | 1.29 | 0.141 | 3.0% | 3.22 | 0% |
| IT Jobs 2026 (vietnamworks) | 965 | 27.0 | 1.31 | 0.154 | 7.0% | 3.20 | 1.3% |
| TopCV 2026 | 609 | 21.5 | 1.43 | 0.211 | **24.0%** | **0.44** | 7.2% |

TopCV 2026 là nguồn nhiễu nhất: khoảng rộng nhất, một phần tư số tin chỉ ghi một đầu, gần như không có kỹ năng, và lương thấp hơn khoảng 5 tr. `source` không phải đặc trưng của mô hình (`CATEGORICAL`/`NUMERIC` trong `salary_model.py`), nên mô hình không tách được nguồn này.

## 3. Sai số của GB theo lát (test, n = 696)

Cột: MAE/MAPE so với trung điểm (metric hiện tại); MAE kỳ vọng so với lương thật T ~ U[low, high]; sàn nhiễu = E|trung điểm − T| = width/4; khoảng cách trung bình từ dự đoán đến khoảng chào (0 nếu nằm trong); tỉ lệ dự đoán nằm trong khoảng.

| Lát | n | MAE trung điểm | MAPE | MAE so với T | Sàn nhiễu | KC đến khoảng | Trong khoảng |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Toàn bộ** | 696 | **5.82** | **20.7%** | 6.17 | **2.03** | 2.76 | 42.2% |
| Hai đầu | 665 | 5.75 | 20.8% | 6.08 | 2.00 | 2.73 | 41.8% |
| Chỉ đầu trên (0.7x) | 26 | 6.61 | 17.8% | 7.42 | 2.77 | 2.95 | 53.8% |
| Chỉ đầu dưới (1.3x) | 5 | 11.19 | 24.4% | 11.45 | 2.82 | 6.49 | 40.0% |
| CareerBuilder 2023 | 7 | 10.66 | 32.0% | 11.62 | 3.73 | 5.42 | 42.9% |
| careerviet | 141 | 5.93 | 20.2% | 6.15 | 1.67 | 3.26 | 36.9% |
| itviec | 125 | 5.53 | 20.2% | 5.77 | 1.75 | 2.77 | 40.0% |
| topcv (IT Jobs) | 155 | 5.27 | 19.9% | 5.57 | 1.88 | 2.39 | 40.6% |
| vietnamworks | 171 | 6.33 | 19.4% | 6.68 | 2.18 | 3.02 | 42.7% |
| TopCV 2026 | 97 | 5.69 | **25.1%** | 6.40 | 2.79 | 1.97 | 54.6% |
| Cao/thấp (1, 1.25] | 263 | 6.73 | 20.3% | 6.85 | 1.47 | 4.16 | 24.3% |
| Cao/thấp (1.25, 1.5] | 320 | 5.36 | 20.2% | 5.72 | 2.06 | 2.28 | 47.8% |
| Cao/thấp (1.5, 2] | 93 | 4.45 | 22.4% | 5.12 | 2.72 | 0.96 | 67.7% |
| Cao/thấp (2, 3] | 20 | 7.57 | 26.6% | 9.24 | 5.84 | 0.49 | 70.0% |

Nhận xét:

- MAE không tăng theo độ rộng khoảng. Tin có khoảng hẹp nhất (≤ 1.25) lại có MAE cao nhất (6.73) và chỉ 24% dự đoán nằm trong khoảng. Sai số bị chi phối bởi thông tin còn thiếu, không bởi nhiễu nhãn.
- MAPE của TopCV 2026 cao nhất (25.1%) dù MAE trung bình, vì lương thấp hơn và nhãn rộng hơn. Đây đúng là lát mà nhiễu nhãn (sàn 2.79) chiếm phần lớn nhất.
- Lát một đầu quá nhỏ trên test (31 tin) để kéo metric tổng. Bỏ hẳn lát này chỉ đổi MAE từ 5.82 xuống 5.75.

## 4. Ước lượng sàn

| Kịch bản | MAE | MAPE | Ý nghĩa |
|---|---:|---:|---|
| Đoán đúng trung điểm, đo so với T ~ U[low, high] | 2.03 | 7.8% | Sàn tuyệt đối do nhãn là khoảng |
| Trung vị nhóm trùng đặc trưng, in-sample | 3.84 | 15.8% | Cận dưới lạc quan với đặc trưng hiện tại |
| Trung vị nhóm trùng đặc trưng, leave-one-out | 5.74 | 23.6% | Ước lượng thực tế, cùng bậc với GB |
| GB hiện tại, so với trung điểm | 5.82 | 20.7% | Metric đang báo cáo |
| GB hiện tại, so với T ~ U[low, high] | 6.17 | — | Sai số thật kỳ vọng với người dùng |

Giới hạn của ước lượng:

- Giả định đều trong khoảng là giả định làm việc. Nếu lương thật dồn về đầu dưới (thường gặp với khoảng chào tuyển), trung điểm bị lệch có hệ thống và sàn so với lương thật cao hơn.
- Nhóm trùng đặc trưng nghiêng về tin ít thông tin (kỹ năng rỗng, TopCV 2026). Với nhóm nhỏ, trung vị leave-one-out cũng thêm nhiễu ước lượng, nên 5.74 hơi bi quan và 3.84 lạc quan.
- MAPE trong `metrics.json` dùng `sklearn.metrics.mean_absolute_percentage_error` (sklearn 1.9.1 trong venv), tính |y − ŷ| / max(ε, |y|) với y là trung điểm, nên các con số MAPE ở đây so sánh trực tiếp được với metric gốc.

## Gợi ý cho các ticket bị chặn (#78, #81)

- Báo thêm metric theo khoảng (khoảng cách đến khoảng chào, tỉ lệ nằm trong khoảng: 42.2%) bên cạnh MAE so với trung điểm. Metric này không phạt mô hình vì độ rộng khoảng.
- Cân nhắc trọng số mẫu theo 1/độ rộng, hoặc thêm cờ "suy ra một đầu" làm đặc trưng. Hệ số 0.7 cho "tới X" đáng kiểm tra lại (tỉ lệ ngầm định 1.43, so với trung vị thực tế 1.29).
- Cải thiện nên đến từ thông tin mới cho các tin đang trùng đặc trưng, không phải từ tinh chỉnh mô hình: GB đã ngang sàn leave-one-out.
