# Công thức

Ký hiệu chung: $s$ là lương thật (triệu đồng/tháng), $\hat{s}$ là lương mô hình dự đoán (lương chào tuyển), $n$ là số tin. Đường dẫn code tính từ `job_market/src/career_market/`.

---

## 1. Đọc lương

### 1.1 Lương trung điểm — `data/rules.py` (`parse_salary`)

$$s = \frac{s_{\text{thấp}} + s_{\text{cao}}}{2}$$

"15 – 25 triệu" → 20 triệu. Mô hình học con số này.

### 1.2 Đổi đơn vị — `data/rules.py`

$$s_{\text{VND}} = \frac{x_{\text{USD}} \times \text{tỷ giá}_{\text{năm}}}{10^6}, \qquad s_{\text{tháng}} = \frac{s_{\text{năm}}}{12}$$

Tỷ giá theo năm đăng tin: 2023 = 23.500; 2024 = 24.500; 2025 = 25.500; 2026 = 26.000. Số từ 100.000 trở lên được coi là đồng và chia $10^6$.

### 1.3 Loại khoảng lương vô nghĩa — `data/rules.py`

$$\text{giữ tin khi}\quad \frac{s_{\text{cao}}}{s_{\text{thấp}}} \le 3 \quad\text{và}\quad 3 \le s \le 150$$

"1 – 40 triệu" (gấp 40 lần) là giá trị điền sẵn của biểu mẫu, không phải lương thật.

### 1.4 Tin chỉ ghi một con số — `data/dataset.py` (`_one_sided_ratios`)

$$\text{"Tới } X\text{"}: s_{\text{thấp}} = \frac{X}{\rho_{\text{nguồn}}}, \qquad \text{"Từ } X\text{"}: s_{\text{cao}} = X \cdot \rho_{\text{nguồn}}$$

$$\rho_{\text{nguồn}} = \operatorname{trung\ vị}\left(\frac{s_{\text{cao}}}{s_{\text{thấp}}}\right) \text{ trên tin tập học cùng nguồn ghi đủ hai đầu}$$

Nguồn có dưới 30 tin như vậy thì dùng trung vị chung. Ví dụ tin ITviec $\rho = 1{,}27$, tin TopCV trong bộ IT Jobs $\rho = 1{,}67$. So sánh với các cách khác: `docs/research/118-single-salary-rules.md`.

## 2. Kinh nghiệm và cấp bậc — `data/rules.py`

| Chuỗi kinh nghiệm | Số năm |
|---|---|
| "Không yêu cầu" | 0 |
| "Dưới X năm" | X / 2 |
| "Trên X năm" | X + 1 |
| "a – b năm" | (a + b) / 2 |

Chức danh không ghi cấp bậc thì suy từ số năm $y$:

$$\text{cấp bậc} = \begin{cases} \text{Fresher} & y < 1 \\ \text{Junior} & 1 \le y < 2{,}5 \\ \text{Middle} & 2{,}5 \le y < 4{,}5 \\ \text{Senior} & y \ge 4{,}5 \end{cases}$$

## 3. Chia dữ liệu theo công ty — `data/dataset.py` (`_split_for`)

$$u = \frac{\operatorname{SHA256}(\text{"42:"} + \text{tên công ty})_{[0:8]}}{\texttt{0xFFFFFFFF}} \in [0, 1]$$

$$\text{tập} = \begin{cases} \text{học} & u < 0{,}70 \\ \text{chọn} & 0{,}70 \le u < 0{,}85 \\ \text{kiểm tra} & u \ge 0{,}85 \end{cases}$$

Cùng tên công ty luôn ra cùng $u$, nên mỗi công ty nằm trọn một tập và chạy lại bao nhiêu lần cũng ra cùng cách chia.

## 4. Mô hình — `model/estimators.py`

### 4.1 Học trên logarit

$$\text{học } f(x) \approx \ln s, \qquad \hat{s} = e^{f(x)}$$

Lệch 5 triệu với người lương 10 triệu (50%) nghiêm trọng hơn với người lương 100 triệu (5%); logarit làm mô hình quan tâm sai số theo **tỉ lệ**.

### 4.2 Ridge có chặn hệ số kỹ năng (`SignedRidge`)

$$\min_{\beta}\; \lVert y - X\beta \rVert^2 + \alpha \lVert \beta \rVert^2 \quad\text{với}\quad \beta_{\text{kỹ năng}} \ge 0$$

Mỗi kỹ năng chỉ được cộng (hoặc cộng 0), không bao giờ trừ lương. $\alpha$ chọn trong {0,3; 1; 3; 10} theo tập chọn.

### 4.3 Gradient Boosting có ràng buộc đơn điệu

Mô hình được chọn. Ràng buộc: $\hat{s}$ không giảm khi tăng kinh nghiệm hoặc bật thêm bất kỳ kỹ năng nào (`monotonic_cst`). Tốc độ học ∈ {0,05; 0,1}, số lá tối đa ∈ {15; 31}, chọn theo tập chọn.

### 4.4 Random Forest bọc "bao đơn điệu" (`SkillEnvelope`)

$$\hat{s}(S) = \max_{T \subseteq S} f(T)$$

$S$ là bộ kỹ năng của hồ sơ. Dự đoán là mức cao nhất của mô hình gốc trên mọi tập con của $S$, nên thêm kỹ năng không bao giờ làm kết quả giảm.

## 5. Chỉ số sai số — `model/training.py` (`scores`)

$$\text{MAE} = \frac{1}{n}\sum_{i=1}^{n} \lvert \hat{s}_i - s_i \rvert \qquad \text{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n} (\hat{s}_i - s_i)^2}$$

$$R^2 = 1 - \frac{\sum_i (s_i - \hat{s}_i)^2}{\sum_i (s_i - \bar{s})^2} \qquad \text{MAPE} = \frac{100}{n}\sum_{i=1}^{n} \frac{\lvert \hat{s}_i - s_i \rvert}{s_i}$$

Mô hình được chọn: MAE 6,49 triệu, R² 0,62, MAPE 23% trên tập kiểm tra. Mốc trung vị: MAE 11,25 triệu.

## 6. Khoảng lương và hiệu chỉnh gross

### 6.1 Tỉ lệ thật / dự đoán — `model/training.py`

$$r_i = \frac{s_i}{\hat{s}_i} \text{ trên tập chọn}, \qquad q_p = \text{phân vị } p \text{ của } \{r_i\}, \; p \in \{10, 25, 50, 75, 90\}$$

### 6.2 Hệ số gross — `model/calibration.py` (ADR 0015)

$$c_{\text{cấp, TP}} = \frac{\text{trung bình gross TopDev}_{\text{cấp, TP}}}{\text{trung bình } (\hat{s} \cdot q_{50}) \text{ trên hồ sơ tập học cùng cấp, TP}}$$

$$c_{\text{vai trò}} = \frac{A_{\text{vai trò}}}{\operatorname{trung\ vị}(\hat{s} \cdot q_{50} \cdot c_{\text{cấp, TP}}) \text{ trên hồ sơ tập học cùng vai trò}}, \qquad c = c_{\text{cấp, TP}} \cdot c_{\text{vai trò}}$$

$A_{\text{vai trò}}$ là trung bình cộng hai trung vị ITviec đã công bố cho vai trò đó (bản 2023–2024 và 2024–2025). Thiếu ô cấp × thành phố thì dùng trung vị hệ số các thành phố cùng cấp; Intern mượn hệ số Fresher.

### 6.3 Khoảng lương hiển thị — `model/advisor.py`

$$\text{khoảng} = \big(\hat{s} \cdot q_{25},\;\; \hat{s} \cdot q_{50},\;\; \hat{s} \cdot q_{75}\big) \times c$$

Ví dụ Backend Junior Hà Nội (Java, SQL): 13,4 – **16,3** – 19,3 triệu, $c = 1{,}22$.

### 6.4 Khoảng rộng hơn cho hồ sơ ít dữ liệu — `model/support.py`

Chỉ hiện con số khi nhóm vai trò × cấp bậc có $n_{\text{học}} \ge 20$ và không trượt chuẩn production. Nếu không:

$$\text{khoảng} = \Big[\min_{g}\, L_g,\; \max_{g}\, H_g\Big] \times c, \quad g \in \{\text{vai trò}, \text{cấp bậc}\}$$

$(L_g, H_g) = (\hat{s} q^{g}_{10}, \hat{s} q^{g}_{90})$ nếu nhóm $g$ có ≥ 20 tin ở tập chọn; nếu không thì là phân vị 10 và 90 của lương thật nhóm $g$ trên tập học.

## 7. Tư vấn — `model/advisor.py`

### 7.1 Mức tăng lương của kỹ năng $k$

$$\Delta_k = \big(\hat{s}(x \cup \{k\}) - \hat{s}(x)\big) \times q_{50} \times c$$

"Nếu tôi giữ nguyên mọi thứ nhưng biết thêm $k$". Chỉ xét $k$ chưa có và xuất hiện ở ≥ 3% tin cùng vai trò; nhờ ràng buộc đơn điệu, $\Delta_k \ge 0$.

### 7.2 Vị trí so với vai trò (phân vị)

$$P = 100 \times \frac{\#\{i \in \text{vai trò} : s_i < \hat{s}\}}{n_{\text{vai trò}}}$$

App ghi "Cao hơn $P$% tin". So trên **lương ghi trong tin** ($\hat{s}$ chưa nhân hệ số gross).

### 7.3 Giá trị kỹ năng trên toàn bộ dữ liệu — `model/training.py` (`skill_value`)

$$\text{chênh trung vị}_k = \operatorname{tv}(s \mid \text{tin có } k) - \operatorname{tv}(s \mid \text{tin không có } k)$$

$$\text{mức tăng mô hình}_k = \frac{1}{\lvert N_k \rvert} \sum_{i \in N_k} \big(\hat{s}(x_i \cup \{k\}) - \hat{s}(x_i)\big)$$

$N_k$ là các tin chưa có $k$. Chỉ tính kỹ năng có ≥ 20 tin.

## 8. Mức quan trọng của đặc trưng — `model/training.py`

$$I_j = R^2_{\text{gốc}} - \frac{1}{5}\sum_{t=1}^{5} R^2\big(\text{cột } j \text{ bị xáo trộn lần } t\big) \quad\text{trên tập chọn}$$

Kinh nghiệm quan trọng nhất ($I \approx 0{,}93$), rồi vai trò, nền tảng, cấp bậc.

## 9. Kiểm định — `model/validation.py`

### 9.1 Hiệu chuẩn khoảng

$$\text{độ phủ}(L) = \frac{1}{n}\sum_{i} \mathbf{1}\Big[\hat{s}_i \, q_{\frac{1-L}{2}} \le s_i \le \hat{s}_i \, q_{\frac{1+L}{2}}\Big] \;\stackrel{?}{\approx}\; L$$

Trên tập kiểm tra: khoảng 50% phủ 51%, khoảng 80% phủ 83%, khoảng 90% phủ 91%.

### 9.2 Bootstrap theo công ty

Lặp $B = 1.000$ lần: bốc ngẫu nhiên có hoàn lại các **công ty** của tập kiểm tra, tính lại chỉ số $m^{(b)}$.

$$\text{khoảng tin cậy 95\%} = \big[\,P_{2{,}5}(m^{(b)}),\; P_{97{,}5}(m^{(b)})\,\big], \qquad p_{\text{thắng}} = \frac{1}{B}\sum_b \mathbf{1}\big[\text{MAE}^{(b)}_{\text{GB}} < \text{MAE}^{(b)}_{\text{khác}}\big]$$

### 9.3 Độ lệch công bằng của nhóm $g$

$$b_g = \frac{100}{n_g}\sum_{i \in g} \frac{\hat{s}_i - s_i}{s_i}$$

$b_g > 0$: đoán cao cho nhóm $g$. Khoảng tin cậy chứa 0 thì chưa có bằng chứng lệch; nhóm dưới 20 tin chỉ báo cáo.

### 9.4 Tương quan Spearman (trang Tổng quan)

$$\rho_s = 1 - \frac{6\sum_i d_i^2}{n(n^2 - 1)}, \quad d_i = \text{hạng}(y_i) - \text{hạng}(s_i)$$

Kinh nghiệm và lương: $\rho_s \approx 0{,}7$.

## 10. Chuẩn production — `model/production.py` (ADR 0014)

$$e_i = 100 \cdot \frac{\lvert \hat{s}_i - s_i \rvert}{s_i}$$

| Chỉ số | Mức chung (so cận bất lợi của bootstrap) | Mức nhóm (≥ 20 tin, so giá trị điểm) |
|---|---|---|
| Trung vị của $e_i$ | ≤ 15% | ≤ 20% |
| Tỉ lệ $e_i \le 20$ | ≥ 65% | ≥ 50% |
| Độ phủ khoảng p10–p90 | 75% – 85% | 70% – 100% |

Mục tiêu dài hạn (mức Glassdoor): trung vị sai số ≤ 10%, tỉ lệ sai ≤ 20% ≥ 75%.

## 11. Kiểm tra thực tế — `model/reality.py`

$$\text{lệch}_j = \frac{\lvert \text{dự đoán}_j - \text{báo cáo}_j \rvert}{\text{báo cáo}_j}$$

Đạt khi $\text{lệch}_j \le 15\%$ ở ≥ 80% ô vai trò (hiện 8/10).

## 12. Vận hành

| Quy tắc | Công thức | Code |
|---|---|---|
| Cổng thay model | Thay khi mô hình mới đạt chuẩn; hoặc cả hai chưa đạt, mô hình mới không kém ở chỉ số chung nào và qua nhiều phạm vi hơn / tốt hơn ở ít nhất một chỉ số | `model/promotion.py` |
| Mẫu kiểm tra nhãn | Tỉ lệ sai $= 100 - 100\cdot\frac{\#\text{đúng}}{\#\text{đã chấm}}$ theo từng loại nhãn | `data/review.py` |
