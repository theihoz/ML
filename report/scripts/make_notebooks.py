"""Sinh 6 notebook trình bày từng tính năng của ứng dụng (job_market/notebooks/tinh_nang_*.ipynb).

Notebook được ghi KHÔNG kèm output (quy ước của repo); tests/test_feature_notebooks.py chạy lại từng cái.
Chạy: python report/scripts/make_notebooks.py job_market/notebooks
"""

import sys
from pathlib import Path

import nbformat as nbf

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

SETUP = """# Thiết lập: dùng đúng thư viện của ứng dụng (job_market/src), dữ liệu và mô hình đã lưu.
import sys
import warnings
from pathlib import Path

ROOT = Path.cwd().resolve()
while not (ROOT / "src" / "career_market").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from career_market.ui import charts  # thư viện biểu đồ chọn backend "Agg" (vẽ cho web)…
%matplotlib inline
# …nên bật lại chế độ inline để biểu đồ hiện trong notebook.
pd.set_option("display.max_colwidth", 80)
pd.set_option("display.float_format", lambda v: f"{v:,.2f}")
"""


def md(text):
    return nbf.v4.new_markdown_cell(text.strip("\n"))


def code(text):
    return nbf.v4.new_code_cell(text.strip("\n"))


def notebook(name, cells):
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.cells = cells
    nbf.write(nb, OUT / name)


# ───────────────────────────────────────────── 1. DỮ LIỆU HUẤN LUYỆN
notebook("tinh_nang_1_du_lieu_huan_luyen.ipynb", [
    md("""
# Tính năng 1 – Trang **Dữ liệu huấn luyện**

Trang này cho thấy dữ liệu mà mô hình học: phễu làm sạch, cách chia train/valid/test và bảng dữ liệu tải về được. Notebook đi lại các bước phía sau, theo mạch **vấn đề → hậu quả nếu để nguyên → lựa chọn → lý do → cái giá**:

1. Dữ liệu thô có những vấn đề gì (đếm lại trên file gốc).
2. **Tin sinh tự động** – phát hiện quan trọng nhất – và vì sao phải loại.
3. Quy tắc chuẩn hóa lương chạy trên ví dụ thật.
4. Phễu làm sạch và chia tập **theo công ty**.

Chi tiết đầy đủ về từng nhãn (vai trò, cấp bậc, kỹ năng) và độ chính xác của bộ gán nhãn nằm ở notebook `gan_nhan_du_lieu.ipynb`. Mã nguồn: `src/career_market/salary_dataset.py`, `pages/dataset.py`.
"""),
    code(SETUP),
    md("""
## 1. Ba nguồn thô và những vấn đề của chúng
"""),
    code("""
import re
import unicodedata
from career_market.paths import data_root

RAW = data_root() / "raw"
topcv = pd.read_csv(RAW / "topcv_jobs.csv")
posts = pd.read_csv(RAW / "vietnam_it_job_posts_v1.csv")
cb = pd.read_csv(RAW / "vietnamese-job-posting.csv")
display(pd.DataFrame({"Bộ dữ liệu": ["TopCV 2026", "IT Job Posts 2026", "CareerBuilder 2023"],
                      "Số dòng": [len(topcv), len(posts), len(cb)], "Số cột": [topcv.shape[1], posts.shape[1], cb.shape[1]]}))

raw_salary = pd.concat([topcv["salary"], posts["salary"], cb["salary"]]).fillna("").astype(str)
# Dữ liệu thô viết dấu tiếng Việt theo hai kiểu Unicode (dựng sẵn và tổ hợp): chuẩn hóa NFC trước khi so khớp.
salary = raw_salary.map(lambda v: unicodedata.normalize("NFC", v)).str.lower()
problems = {
    "Ghi 'thỏa thuận / thương lượng / cạnh tranh'": salary.str.contains("thỏa thuận|thoả thuận|thương lượng|cạnh tranh"),
    "Dấu tiếng Việt kiểu tổ hợp (nhìn giống, khác byte)": raw_salary != raw_salary.map(lambda v: unicodedata.normalize("NFC", v)),
    "Lỗi chính tả 'triẹu'": salary.str.contains("triẹu"),
    "Lương bằng USD": salary.str.contains(r"\\$|usd"),
    "Lương theo năm": salary.str.contains(r"/\\s*năm"),
    "Khoảng giả '1 triệu - 40 triệu'": salary.str.contains(r"^1 tri[ẹệ]u - 40 tri[ẹệ]u"),
}
pd.DataFrame({"Vấn đề": problems.keys(), "Số dòng": [int(m.sum()) for m in problems.values()]}).assign(
    **{"Tỉ lệ": lambda t: (t["Số dòng"] / len(salary) * 100).round(1).astype(str) + "%"})
"""),
    md("""
**Khoảng lương giả** "1 – 40 triệu" là giá trị mặc định của biểu mẫu đăng tin. Trung điểm 20,5 triệu trông rất bình thường nên máy không báo lỗi mà lặng lẽ học sai – loại lỗi nguy hiểm nhất. Quy tắc: bỏ mọi khoảng có cận trên gấp hơn 3 lần cận dưới.

## 2. Phát hiện lớn nhất: 2.400 tin sinh tự động

**Dấu hiệu đầu tiên:** ngày đăng ở ba nền tảng TopCV, VietnamWorks, CareerViet rải đều 2018–2025 – thị trường thật không bao giờ đều như vậy. Ban đầu nhóm chỉ coi đây là cột hỏng. Điều tra tiếp cho thấy cả nhóm tin đó có chung các dấu hiệu dưới đây.
"""),
    code("""
from career_market.data.rules import is_synthetic

synthetic = posts["source_url"].map(is_synthetic)
print("Số tin có đường dẫn dạng …-hist…:", int(synthetic.sum()))
display(posts[synthetic]["source_platform"].value_counts().rename("Số tin theo nền tảng").to_frame())
display(pd.DataFrame({
    "Tin sinh tự động": [posts[synthetic]["requirements"].notna().mean() * 100],
    "Tin thật": [posts[~synthetic]["requirements"].notna().mean() * 100],
}, index=["% có mô tả yêu cầu"]))
posts[synthetic][["title", "source_url", "skills"]].head(5)
"""),
    code("""
years = pd.DataFrame({
    "Tin sinh tự động": posts[synthetic]["posted_at"].astype(str).str[:4].value_counts(),
    "Tin thật": posts[~synthetic]["posted_at"].astype(str).str[:4].value_counts(),
}).fillna(0).sort_index()
ax = years.plot.bar(figsize=(9, 3.5), color=["#f97316", "#2563eb"], title="Số tin theo năm đăng ghi trong dữ liệu")
ax.set(xlabel="", ylabel="Số tin");
"""),
    md("""
- **Vấn đề:** 2.400 tin (đúng 800 mỗi nền tảng) có đường dẫn `…-hist…`, ngày đăng rải đều, kỹ năng ngẫu nhiên (Android Developer có Swift và React), không có mô tả. Chúng chiếm 54% số tin có nhãn trước khi loại.
- **Hậu quả nếu giữ:** tin giả dễ đoán hơn tin thật nên làm điểm đẹp giả – mô hình cũ có trung vị sai số 16,5% trên tập test lẫn tin sinh nhưng 18,0% trên riêng tin thật. Giống ôn thi bằng bộ đề do máy bịa.
- **Lựa chọn:** loại hẳn (thay vì chỉ sửa cột ngày hoặc đánh dấu).
- **Cái giá:** mất hơn nửa dữ liệu; tập test còn 288 tin.

## 3. Chuẩn hóa lương – mỗi quy tắc có lý do

| Dạng ghi | Quy tắc | Vì sao |
|---|---|---|
| "15 - 25 triệu" | trung điểm 20 | Nhà tuyển dụng hay nói "lương khoảng 20 triệu"; cận trên là mức trần |
| "Tới 30 triệu" / "Từ 20 triệu" | suy đầu còn lại bằng **hệ số cao/thấp của từng nguồn** (học trên train) | Mỗi trang có thói quen ghi khoảng khác nhau; hệ số cố định 0,7 ban đầu không đúng cho mọi trang |
| USD / theo năm | × tỷ giá năm dữ liệu / ÷ 12 | Tránh "1.000 USD" thành 1.000 triệu |
| Khoảng > 3 lần | loại | Một vị trí hiếm khi chênh quá 3 lần; khoảng rộng hơn là né công bố |
"""),
    code("""
import json
from career_market.data.rules import parse_salary
from career_market.paths import dataset_path

summary = json.loads(dataset_path().with_suffix(".json").read_text(encoding="utf-8"))
ratios = summary["one_sided_ratio"]
display(pd.Series(ratios, name="Hệ số cao/thấp (học trên train)").to_frame())

examples = ["15 - 25 triệu", "Lương: 10 Tr - 15 Tr VND", "$ 1,000-1,500 /tháng", "240tr-360tr ₫/năm", "1 triẹu - 40 triẹu/tháng", "Thỏa thuận"]
rows = [{"Chuỗi gốc": t, "Kết quả (thấp, cao, trung điểm)": parse_salary(t, 2026) or "loại khỏi nhãn"} for t in examples]
for text in ["Tới 30 triệu", "Từ 20 triệu"]:
    for source in ["IT Jobs 2026 (itviec)", "TopCV 2026"]:
        rows.append({"Chuỗi gốc": f"{text}  [{source}]", "Kết quả (thấp, cao, trung điểm)": parse_salary(text, 2026, ratio=ratios[source])})
pd.DataFrame(rows)
"""),
    md("""
## 4. Phễu làm sạch và chia tập theo công ty

**Vì sao chia theo công ty?** Một công ty đăng hàng chục tin gần giống nhau. Chia ngẫu nhiên thì mô hình chỉ cần "nhớ" công ty là đoán đúng – như ôn đúng đề sẽ thi. Câu hỏi thật của người dùng là về **công ty mới**, nên tập test phải gồm công ty mô hình chưa từng gặp. Hàm băm SHA-256 trên tên công ty (seed 42) giúp kết quả chia luôn tái lập được.
"""),
    code("""
from career_market.data.dataset import load_dataset

funnel = summary["funnel"]
steps = pd.DataFrame({
    "Bước": ["Đọc ba nguồn (CareerBuilder chỉ nhóm CNTT)", "Sau khi loại tin sinh tự động", "Có lương đọc được", "Thuộc 23 vai trò CNTT", "Sau khử trùng lặp"],
    "Số tin": [funnel["raw"], funnel["raw"] - funnel["synthetic_removed"], funnel["has_salary"], funnel["it_role"], funnel["deduplicated"]],
})
steps["Tỉ lệ"] = (steps["Số tin"] / funnel["raw"] * 100).round(1).astype(str) + "%"
display(steps)

frame = load_dataset()
table = frame.groupby("split").agg(**{"Số tin": ("row_id", "size"), "Số công ty": ("company_key", "nunique")}).loc[["train", "valid", "test"]]
table["Tỉ lệ tin"] = (table["Số tin"] / len(frame) * 100).round(1).astype(str) + "%"
display(table)
groups = {s: set(frame.loc[frame["split"] == s, "company_key"]) for s in ["train", "valid", "test"]}
print("Công ty xuất hiện ở hai tập:", len(groups["train"] & groups["valid"]) + len(groups["train"] & groups["test"]) + len(groups["valid"] & groups["test"]))
print("Còn tin sinh tự động trong bộ dữ liệu sạch:", int(frame["source_url"].map(is_synthetic).sum()))
"""),
    md("""
Hai biểu đồ dưới đây chính là hai biểu đồ trên trang Dữ liệu huấn luyện.
"""),
    code("""
charts.split_by_role(frame);
"""),
    code("""
charts.salary_distribution(frame);
"""),
    md("""
## Kết luận
- Mỗi lỗi của dữ liệu thô có một quy tắc xử lý minh bạch, kiểm thử được.
- Bài học lớn nhất: *nhiều dữ liệu chỉ có giá trị khi dữ liệu là thật*. Loại 2.400 tin sinh tự động làm sai số tăng nhưng trung thực.
- Chia theo công ty là quyết định phương pháp quan trọng nhất: mọi con số đánh giá đều đo trên công ty chưa từng gặp.
"""),
])

# ───────────────────────────────────────────── 2. TỔNG QUAN
notebook("tinh_nang_2_tong_quan_thi_truong.ipynb", [
    md("""
# Tính năng 2 – Trang **Tổng quan** (dashboard thị trường)

4 thẻ KPI và 6 biểu đồ mô tả thị trường trên 1.735 tin thật có lương. Phần này chỉ mô tả dữ liệu, không dùng mô hình (trừ thẻ sai số). Notebook tính lại từng con số và vẽ lại từng biểu đồ, kèm insight và lý do chọn loại biểu đồ.

Mã nguồn: `pages/overview.py`, `src/career_market/salary_charts.py`.
"""),
    code(SETUP),
    code("""
from career_market.data.dataset import load_dataset
from career_market.model.training import load_report

frame = load_dataset()
report = load_report()
facts = charts.summary(frame)
selected = report["models"][report["selected"]]
pd.Series({
    "Số tin có lương": f"{facts['postings']:,}", "Số công ty": facts["companies"],
    "Trung vị lương (triệu)": round(facts["median"], 1), "Trung bình (triệu)": round(facts["mean"], 1), "P90 (triệu)": round(facts["p90"], 1),
    "Top 3 công nghệ": " · ".join(charts.skill_table(frame).nlargest(3, "postings")["skill"]),
    "Số vai trò": facts["roles"], "Mô hình tốt nhất": selected["label"],
    "MAE test (triệu)": round(selected["test"]["MAE"], 2), "R² test": round(selected["test"]["R2"], 2),
}, name="KPI").to_frame()
"""),
    md("""
### Vì sao dùng **trung vị**?
Một phòng có 9 người lương 20 triệu và một giám đốc 200 triệu: trung bình 38 triệu nhưng không ai trong 9 người kia nhận gần 38 triệu. Trung vị (20 triệu) mô tả đúng "người bình thường".
"""),
    code("""
team = pd.Series([20] * 9 + [200])
print(f"Ví dụ: trung bình {team.mean():.0f} · trung vị {team.median():.0f} triệu")
print(f"Dữ liệu thật: trung bình {frame['salary'].mean():.1f} · trung vị {frame['salary'].median():.1f} · độ lệch phải (skew) {frame['salary'].skew():.2f}")
"""),
    md("""
## 1. Công nghệ có nhu cầu – và lương theo công nghệ
Biểu đồ **cột ngang** vì có nhiều hạng mục tên dài. Trang hiển thị toàn bộ kỹ năng; ở đây vẽ 15 kỹ năng đầu cho gọn.
"""),
    code("""
charts.top_skill_demand(frame, limit=15);
"""),
    code("""
charts.top_skill_salary(frame, limit=15);
"""),
    code("""
table = charts.skill_table(frame)
pd.concat([
    table.nlargest(8, "postings")[["skill", "postings", "median"]].reset_index(drop=True).add_prefix("Phổ biến: "),
    table[table["postings"] >= 30].nlargest(8, "median")[["skill", "postings", "median"]].reset_index(drop=True).add_prefix("Lương cao (≥30 tin): "),
], axis=1)
"""),
    md("""
**Insight:** kỹ năng phổ biến nhất (JavaScript, Java, React) không phải kỹ năng trả cao nhất (AWS, LLM/GenAI, Next.js). Đây mới là mô tả: tin đòi AWS có thể là tin Senior. Mô hình ở tính năng 4 tách hai yếu tố này.

## 2. Kinh nghiệm & thu nhập
**Boxplot theo nhóm năm + đường trung vị** để thấy cả xu hướng lẫn độ phân tán. Độ liên hệ đo bằng **Spearman** vì quan hệ không phải đường thẳng và có ngoại lai.
"""),
    code("""
from scipy.stats import spearmanr

known = frame.dropna(subset=["experience_years"])
print(f"Spearman ρ = {spearmanr(known['experience_years'], known['salary']).statistic:.2f} trên {len(known):,} tin có kinh nghiệm")
by_year = known.groupby(pd.cut(known["experience_years"], charts.EXPERIENCE_BINS, labels=charts.EXPERIENCE_LABELS), observed=False)["salary"]
display(pd.DataFrame({"Số tin": by_year.size(), "Trung vị (triệu)": by_year.median()}).T)
charts.experience_salary(frame);
"""),
    md("""
Bước nhảy lớn nhất giữa **4 và 5 năm** (Middle → Senior): lên Senior là đổi vai trò, không chỉ thêm một năm.

## 3. Khu vực
"""),
    code("""
regions = frame.groupby("region")["salary"].agg(["size", "median"]).sort_values("size", ascending=False)
regions["Tỉ lệ tin"] = (regions["size"] / len(frame) * 100).round(1).astype(str) + "%"
display(regions.rename(columns={"size": "Số tin", "median": "Trung vị"}))
charts.region_salary(frame);
"""),
    md("""
⚠️ Không kết luận "TP. HCM lương thấp hơn": công ty ở TP. HCM hay ghi "Thương lượng" nên mẫu nhỏ và có thể lệch.

## 4. Vai trò, và vai trò × khu vực
**Heatmap** thể hiện bảng hai chiều; ô dưới 3 tin để trống có chủ đích.
"""),
    code("""
charts.role_salary(frame);
"""),
    code("""
charts.role_region_heatmap(frame);
"""),
    md("""
## Kết luận
1. Kinh nghiệm là yếu tố mạnh nhất; bước nhảy lớn nhất khi lên Senior.
2. Data Engineer, DevOps, quản lý kỹ thuật trả cao hơn rõ lập trình phổ thông (nhưng vài nhóm rất ít tin).
3. Kỹ năng phổ biến ≠ kỹ năng trả cao.
4. So sánh khu vực phải kèm cảnh báo về tỉ lệ công bố lương.
"""),
])

# ───────────────────────────────────────────── 3. THỊ TRƯỜNG
notebook("tinh_nang_3_thi_truong_viec_lam.ipynb", [
    md("""
# Tính năng 3 – Trang **Thị trường việc làm**

Trang lọc tin tuyển dụng có công bố lương theo **nguồn**, **vai trò** và **khu vực**, rồi cho thấy kỹ năng nào được yêu cầu nhiều nhất và kỹ năng nào đi kèm mức lương cao. Trang chỉ mô tả dữ liệu, không dùng mô hình.

Dữ liệu là bộ salary-v2 (1.735 tin thật) giống trang Tổng quan; bộ lọc biến bức tranh chung thành câu trả lời riêng cho từng nghề, từng nơi.

Mã nguồn: `pages/market.py`, `src/career_market/ui/cache.py` (`filter_postings`), `src/career_market/ui/charts.py`.
"""),
    code(SETUP),
    code("""
from career_market.data.dataset import load_dataset

frame = load_dataset()


def filter_postings(sources=(), roles=(), regions=()):
    \"\"\"Giống trang web: danh sách rỗng nghĩa là không lọc.\"\"\"
    mask = pd.Series(True, index=frame.index)
    if sources:
        mask &= frame["source"].isin(sources)
    if roles:
        mask &= frame["role"].isin(roles)
    if regions:
        mask &= frame["region"].isin(regions)
    return frame[mask]


print(f"{len(frame):,} tin · {frame['source'].nunique()} nguồn · {frame['role'].nunique()} vai trò")
"""),
    md("""
## 1. Kỹ năng theo bộ lọc
Quy ước: bộ lọc rỗng = không lọc; một tin chỉ tính một lần.
"""),
    code("""
cases = {
    "Toàn bộ": dict(),
    "Backend": dict(roles=["Backend Developer"]),
    "Data Engineer": dict(roles=["Data Engineer"]),
    "TP. Hồ Chí Minh": dict(regions=["TP. Hồ Chí Minh"]),
    "Chỉ ITviec": dict(sources=["IT Jobs 2026 (itviec)"]),
}
rows = []
for name, kwargs in cases.items():
    view = filter_postings(**kwargs)
    table = charts.skill_table(view).sort_values("postings", ascending=False)
    rows.append({
        "Bộ lọc": name,
        "Số tin": len(view),
        "Tin có kỹ năng": int((view["skill_count"] > 0).sum()),
        "Trung vị lương": view["salary"].median(),
        "Top 3 kỹ năng": ", ".join(table["skill"].head(3)) if len(table) else "—",
    })
pd.DataFrame(rows)
"""),
    code("""
view = filter_postings(roles=["Backend Developer"])
charts.top_skill_demand(view, limit=20)
"""),
    md("""
## 2. Kỹ năng đi kèm lương cao
Thanh xám là kỹ năng có dưới 10 tin trong phần đã lọc: ít dữ liệu, không nên kết luận.
"""),
    code("""
charts.top_skill_salary(view, limit=20, min_postings=10)
"""),
    md("""
⚠️ Nguồn TopCV 2026 **chỉ có chức danh**, không có mô tả công việc, nên kỹ năng được đoán từ tiêu đề: "tin có kỹ năng" thấp không có nghĩa là tin không đòi kỹ năng.

## Kết luận
- Bộ lọc biến bức tranh chung thành câu trả lời riêng cho từng nghề, từng nơi.
- Kỹ năng phổ biến chưa chắc là kỹ năng trả cao.
- Mức lương gắn với kỹ năng chỉ là tương quan, không chứng minh kỹ năng gây tăng lương.
"""),
])

# ───────────────────────────────────────────── 4. MÔ HÌNH
notebook("tinh_nang_4_danh_gia_mo_hinh.ipynb", [
    md("""
# Tính năng 4 – Trang **Đánh giá mô hình** (phần 1: huấn luyện và so sánh)

Mô hình nào được chọn và vì sao, sai số trên tập test, thực tế so với dự đoán, đặc trưng quan trọng, giá trị gia tăng của kỹ năng, sai số theo vai trò. Phần kiểm định độ tin cậy và chuẩn production của cùng trang ở notebook tính năng 5.

Mã nguồn: `src/career_market/salary_model.py`, `pages/evaluation.py`.
"""),
    code(SETUP),
    code("""
from career_market.data.dataset import load_dataset
from career_market.model.estimators import MODEL_LABELS, build_model, feature_frame
from career_market.model.training import load_report, load_skill_value, scores
from career_market.paths import artifacts_dir

frame = load_dataset()
report = load_report()
parts = {s: frame[frame["split"] == s] for s in ["train", "valid", "test"]}
print({s: len(p) for s, p in parts.items()})
"""),
    md("""
## 1. Đầu vào – và những gì cố ý **không** đưa vào
Đầu vào: vai trò, khu vực, cấp bậc, **nền tảng đăng tin, hình thức làm việc, loại công ty**, số năm kinh nghiệm, năm dữ liệu, 4 cờ từ khóa chức danh, 69 cột kỹ năng. Không đưa tên công ty, tiêu đề gốc, chuỗi lương: nếu có tên công ty, mô hình sẽ học "công ty X trả cao" – vô dụng với công ty mới.
"""),
    code("""
X = feature_frame(parts["train"])
print("Số cột đầu vào trước khi mã hóa:", X.shape[1])
X.iloc[:3, :12]
"""),
    md("""
## 2. Bốn ứng viên – như bốn cách con người định lương

| Mô hình | Giống như ngoài đời | Điểm yếu |
|---|---|---|
| **Mốc trung vị** | Ai hỏi cũng trả lời "khoảng 25 triệu" | Thước đo tối thiểu |
| **Ridge** | Bảng giá cộng dồn: Backend +2, mỗi năm +3, AWS +1 | Không hiểu "tùy hoàn cảnh" |
| **Random Forest** | Hỏi 300 chuyên viên, mỗi người xem một phần hồ sơ, rồi lấy trung bình | Ngoài đời không ai có 300 góc nhìn độc lập; từng người dễ "thuộc lòng" |
| **Gradient Boosting** | Hội đồng nối tiếp: người sau chỉ sửa chỗ người trước sai | Khó giải thích hơn Ridge |

**Ba nguyên tắc huấn luyện:** học trên logarit của lương (lệch 5 triệu với người lương 10 triệu nghiêm trọng hơn với người 100 triệu); chọn mô hình bằng MAE trên valid, khóa tiêu chí trước; tập test chỉ mở một lần.
"""),
    code("""
y = parts["train"]["salary"]
print(f"Skew của lương: {y.skew():.2f} → sau logarit: {np.log(y).skew():.2f}")
rows = [{"Mô hình": MODEL_LABELS[n], "Siêu tham số": t["params"], "MAE valid": t["valid_MAE"]} for n, trials in report["tuning"].items() for t in trials]
tuning = pd.DataFrame(rows)
tuning.assign(**{"Chọn": np.where(tuning.groupby("Mô hình")["MAE valid"].transform("min") == tuning["MAE valid"], "✓", "")})
"""),
    md("""
## 3. Luật đời thường: thêm kinh nghiệm hoặc kỹ năng không làm giảm lương

**Vấn đề (06/11):** thêm Java vào hồ sơ Backend 5 năm làm lương dự đoán giảm từ 47,7 xuống 42,3 triệu. Mô hình không lỗi lập trình mà học đúng dữ liệu: cột kỹ năng là **yêu cầu của tin**, và tin liệt kê nhiều kỹ năng thường là tin junior/tuyển hàng loạt. Bảng dưới kiểm tra điều đó trên dữ liệu thật hiện tại:
"""),
    code("""
backend = frame[frame["role"] == "Backend Developer"]
bins = pd.cut(backend["skill_count"], [-1, 0, 2, 4, 6, 30], labels=["0", "1–2", "3–4", "5–6", "7+"])
backend.groupby(bins, observed=False)["salary"].agg(["size", "median"]).rename(columns={"size": "Số tin", "median": "Trung vị lương"}).T
"""),
    md("""
**Lựa chọn:** bỏ đặc trưng "số kỹ năng"; Gradient Boosting có ràng buộc đơn điệu tăng cho kinh nghiệm và 69 cột kỹ năng; Ridge chặn hệ số kỹ năng ≥ 0; Random Forest được bọc "bao đơn điệu". Kiểm tra trên mô hình đã lưu:
"""),
    code("""
from career_market.model.advisor import predict_profile

base = {"role": "Backend Developer", "region": "Hà Nội", "experience_years": 5}
pd.DataFrame([{"Mô hình": MODEL_LABELS[n],
               "Không kỹ năng": predict_profile({**base, "skills": []}, n)["predicted"],
               "+ Java": predict_profile({**base, "skills": ["Java"]}, n)["predicted"],
               "+ Java, Spring Boot, Docker, AWS": predict_profile({**base, "skills": ["Java", "Spring Boot", "Docker", "AWS"]}, n)["predicted"]}
              for n in ["GradientBoosting", "RandomForest", "Ridge"]]).set_index("Mô hình")
"""),
    md("""
## 4. Tái lập kết quả: huấn luyện lại Gradient Boosting với tham số đã chọn
"""),
    code("""
params = report["models"]["GradientBoosting"]["params"]
model = build_model("GradientBoosting", **params).fit(feature_frame(parts["train"]), parts["train"]["salary"])
again = {s: scores(parts[s]["salary"], model.predict(feature_frame(parts[s])))["MAE"] for s in ["train", "valid", "test"]}
pd.DataFrame({"Fit lại trong notebook": again, "Trong metrics.json": {s: report["models"]["GradientBoosting"][s]["MAE"] for s in again}})
"""),
    md("""
## 5. Kết quả trên ba tập
"""),
    code("""
rows = [{"Mô hình": v["label"], "MAE train": v["train"]["MAE"], "MAE valid": v["valid"]["MAE"], "MAE test": v["test"]["MAE"],
         "RMSE test": v["test"]["RMSE"], "R² test": v["test"]["R2"], "MAPE test %": v["test"]["MAPE"]} for v in report["models"].values()]
display(pd.DataFrame(rows).set_index("Mô hình"))
print("Được chọn theo MAE valid:", MODEL_LABELS[report["selected"]])
charts.model_comparison(report);
"""),
    md("""
- Gradient Boosting thấp nhất trên valid → được chọn **trước khi mở test**; trên test vẫn tốt nhất.
- Khoảng cách train – valid của Gradient Boosting lớn nhất: với 1.169 tin train, mô hình học thuộc một phần.
- Các con số cao hơn phiên bản có lẫn tin sinh tự động (MAE 5,82) vì tin thật khó đoán hơn – hai con số không so trực tiếp được.

## 6. Mô hình sai ở đâu?
"""),
    code("""
pred = pd.read_csv(artifacts_dir() / "test_predictions.csv")
error = (pred["predicted"] - pred["salary"]).abs() / pred["salary"]
print(f"Một nửa số tin test lệch dưới {error.median():.1%}; {(error <= 0.2).mean():.0%} lệch không quá 20%")
charts.actual_vs_predicted(pred);
"""),
    code("""
charts.error_by_role(pred);
"""),
    md("""
Sai số lớn nhất ở Tech Lead/Architect và quản lý: lương ở startup 20 người khác xa tập đoàn 5.000 người dù cùng chức danh – quy mô công ty không có trong dữ liệu.

## 7. Yếu tố quyết định lương và kỹ năng đáng học
**Permutation importance:** xáo trộn một cột rồi xem mô hình kém đi bao nhiêu – như cho một cầu thủ nghỉ một trận để biết anh ta quan trọng thế nào.
"""),
    code("""
charts.feature_importance(report);
"""),
    code("""
value = load_skill_value()
display(value[["skill", "postings", "premium_median", "model_uplift"]].rename(columns={
    "skill": "Kỹ năng", "postings": "Số tin", "premium_median": "Chênh trung vị thô", "model_uplift": "Mức tăng mô hình"}).head(12))
print("Kỹ năng có mức tăng âm:", int((value["model_uplift"] < 0).sum()))
charts.skill_uplift(value);
"""),
    md("""
⚠️ Mức tăng là phép thử "nếu như" trên mô hình học từ tin tuyển dụng – **tương quan, không phải nhân quả**.
"""),
])

# ───────────────────────────────────────────── 5. KIỂM ĐỊNH & CHUẨN PRODUCTION
notebook("tinh_nang_5_kiem_dinh_va_chuan_production.ipynb", [
    md("""
# Tính năng 5 – Trang **Đánh giá mô hình** (phần 2: độ tin cậy và chuẩn production)

Bốn câu hỏi mà một con số MAE không trả lời được:
1. **Hiệu chuẩn:** nói "80%" thì có đúng 80%?
2. **Bootstrap:** mô hình thắng thật hay nhờ may?
3. **Công bằng:** có đoán lệch có hệ thống cho nhóm nào? Còn giới tính?
4. **Chuẩn production:** đã đủ tốt để đưa cho người dùng thật chưa?

Mã nguồn: `salary_validation.py`, `production_standard.py`, `prediction_support.py`, `model_promotion.py`.
"""),
    code(SETUP),
    code("""
from career_market.data.dataset import load_dataset
from career_market.model.estimators import MODEL_LABELS, feature_frame
from career_market.model.training import load_model, load_production
from career_market.model.validation import interval_ratios, load_validation

frame = load_dataset()
validation = load_validation()
production = load_production()
model, name, report = load_model()
valid = frame[frame["split"] == "valid"].reset_index(drop=True)
test = frame[frame["split"] == "test"].reset_index(drop=True)
valid_pred = model.predict(feature_frame(valid))
test_pred = model.predict(feature_frame(test))
print(MODEL_LABELS[name], "| valid", len(valid), "| test", len(test), "| công ty test", test["company_key"].nunique())
"""),
    md("""
## 1. Hiệu chuẩn – "dự báo thời tiết 80%"
Nếu đài nói "80% khả năng mưa" cho 100 ngày, đài tốt phải có ~80 ngày mưa thật. Khoảng 80% của ứng dụng = dự đoán × [p10; p90] của tỉ lệ *lương thật / dự đoán* trên valid; kiểm tra trên test chưa dùng. Dùng **tỉ lệ** chứ không ± số cố định vì sai số với người lương 80 triệu lớn hơn với người 15 triệu.
"""),
    code("""
low, high = interval_ratios(valid["salary"].to_numpy(), valid_pred, 0.8)
inside = (test["salary"] >= test_pred * low) & (test["salary"] <= test_pred * high)
print(f"Khoảng 80% = dự đoán × [{low:.2f} ; {high:.2f}] → bao phủ {inside.mean():.1%} lương thật trên test")
display(pd.DataFrame(validation["calibration"]["levels"])[["level", "coverage", "mean_width"]].rename(
    columns={"level": "Tuyên bố", "coverage": "Thực tế", "mean_width": "Độ rộng TB (triệu)"}))
display(pd.DataFrame(validation["calibration"]["by_salary_band"]).rename(columns={"group": "Nhóm lương", "n": "Số tin", "coverage": "Bao phủ 80%"}))
charts.reliability(validation["calibration"]);
"""),
    md("""
Khoảng hơi **rộng hơn cần** (thận trọng) ở mức chung, nhưng chỉ đúng ~72% ở nhóm lương cao.

## 2. Bootstrap theo công ty – "thi lại 1.000 lần với đề khác"
Rút ngẫu nhiên có hoàn lại các **công ty** của tập test (không rút từng tin vì tin cùng công ty giống nhau), chấm lại 1.000 lần. So **theo cặp** trên cùng một đề.
"""),
    code("""
boot = validation["bootstrap"]
display(pd.DataFrame({MODEL_LABELS[n]: {"MAE": v["MAE"]["point"], "KTC 95% thấp": v["MAE"]["ci95"][0], "KTC 95% cao": v["MAE"]["ci95"][1]}
                      for n, v in boot["models"].items()}).T)
display(pd.DataFrame({MODEL_LABELS[n]: {"Chênh MAE TB": d["mean"], "KTC thấp": d["ci95"][0], "KTC cao": d["ci95"][1], "Tỉ lệ GB tốt hơn": d["p_better"]}
                      for n, d in boot["differences"].items()}).T)
charts.bootstrap_differences(boot, MODEL_LABELS);
"""),
    md("""
Gradient Boosting thắng Ridge và Random Forest ở khoảng 85–88% số đề, nhưng khoảng 95% của chênh lệch **vẫn chứa 0** → trên 288 tin thật, **chưa đủ bằng chứng** để khẳng định nó tốt hơn hẳn. (Trên dữ liệu cũ lẫn tin sinh, con số này là 100% – đẹp giả.) Với mốc trung vị thì thắng chắc chắn.

## 3. Công bằng theo nhóm
Chiếc cân lệch 1 kg với mọi người vẫn "công bằng"; chỉ lệch với người thấp là thiên vị. Độ lệch nhóm = trung bình (dự đoán − thật) / thật; khoảng tin cậy chứa 0 → chưa có bằng chứng lệch; nhóm < 20 tin chỉ báo cáo.
"""),
    code("""
def fairness_table(key):
    g = pd.DataFrame(validation["fairness"][key]["groups"])
    g["KTC 95%"] = g["bias_pct_ci95"].map(lambda c: f"{c[0]:+.1f} → {c[1]:+.1f}")
    g["Kết luận"] = np.where(~g["enough"], "ít mẫu – không kết luận",
                    np.where(g["bias_pct_ci95"].map(lambda c: c[0] > 0), "đoán CAO có hệ thống",
                    np.where(g["bias_pct_ci95"].map(lambda c: c[1] < 0), "đoán THẤP có hệ thống", "không có bằng chứng lệch")))
    return g[["group", "n", "MAPE", "bias_pct", "KTC 95%", "Kết luận"]].rename(columns={"group": validation["fairness"][key]["label"], "n": "Số tin", "bias_pct": "Độ lệch %"})

print(f"Độ lệch toàn mô hình: {((test_pred - test['salary']) / test['salary']).mean() * 100:+.1f}% (hệ quả của việc học trên logarit)")
display(fairness_table("region"))
display(fairness_table("level"))
charts.fairness_bias(validation["fairness"]["level"]);
"""),
    code("""
display(fairness_table("platform"))
gender = validation["gender"]
print(f"Giới tính: dữ liệu không có giới tính người được tuyển, mô hình không dùng giới tính. Tin có điều kiện giới tính: {gender['mentioned']} / {len(frame):,}")
pd.DataFrame(gender["examples"])[["title", "source", "gender_requirement", "salary"]]
"""),
    md("""
**Junior bị đoán cao ~7%** (khoảng tin cậy không chứa 0): người mới đi làm nên trừ hao. Giới tính **không đo được** – nói "mô hình công bằng giới" sẽ không trung thực; điều kiện giới tính trong tin là dấu hiệu phân biệt đối xử theo Bộ luật Lao động 2019.

## 4. Chuẩn production – theo cách Glassdoor, LinkedIn công bố
Ba chỉ số dễ hiểu: **trung vị sai số %**, **tỉ lệ dự đoán sai ≤ 20%**, **độ phủ khoảng p10–p90**. Ngưỡng chung so bằng **cận bất lợi** của khoảng bootstrap (không "đậu nhờ may"); ngưỡng nhóm so bằng giá trị điểm.
"""),
    code("""
display(pd.DataFrame(production["thresholds"]).T)
rows = [{"Chỉ số": k, "Giá trị": m["point"], "KTC 95%": f"{m['ci95'][0]:.1f} – {m['ci95'][1]:.1f}", "Ngưỡng": m["threshold"], "Đạt": m["pass"]}
        for k, m in production["overall"]["metrics"].items()]
display(pd.DataFrame(rows))
groups = [{"Phạm vi": f"{dim}: {g['group']}", "Số tin test": g["n"], "Kết quả": g["status"],
           **{k: round(m["point"], 1) for k, m in g.get("metrics", {}).items()}}
          for dim in ("role", "level") for g in production[dim] if g["status"] != "not_scored"]
display(pd.DataFrame(groups))
print("Đạt chuẩn production:", production["production_ready"], "| nhóm trượt:", production["failing"])
"""),
    md("""
**Mô hình chưa đạt chuẩn.** Vì vậy ứng dụng: (1) ghi rõ "kết quả mang tính tham khảo"; (2) chỉ hiện **con số** khi nhóm vai trò × cấp bậc có ≥ 20 tin train và không trượt chuẩn, còn lại chỉ hiện **khoảng mở rộng**; (3) khi huấn luyện lại, mô hình mới chỉ thay mô hình cũ nếu qua **cổng** (đạt chuẩn, hoặc cả hai chưa đạt mà mô hình mới không tệ hơn ở chỉ số chung nào và qua nhiều phạm vi hơn / tốt hơn hẳn ở ít nhất một chỉ số).
"""),
    code("""
support = report["support"]["cohort_train_rows"]
cohorts = pd.Series(support, name="Số tin train").sort_values(ascending=False)
print(f"{(cohorts >= 20).sum()} / {len(cohorts)} nhóm vai trò × cấp bậc đủ 20 tin train để hiện con số")
cohorts.head(12).to_frame()
"""),
])

# ───────────────────────────────────────────── 6. TƯ VẤN
notebook("tinh_nang_6_tu_van_du_doan_luong.ipynb", [
    md("""
# Tính năng 6 – Trang **Tư vấn & dự đoán lương** (trang chủ)

User story: *"Tôi muốn nhập kỹ năng và kinh nghiệm của mình; phần mềm dựa vào mô hình đã huấn luyện sẵn sẽ dự đoán mức lương và tư vấn các kỹ năng nên cải thiện."*

Người dùng nhập vai trò, khu vực, số năm kinh nghiệm, kỹ năng (và tùy chọn chức danh, loại công ty, hình thức làm việc) → nhận **khoảng lương 80%**, **mức điển hình** (nếu đủ dữ liệu), tối đa **5 kỹ năng nên học** và **lộ trình theo kinh nghiệm**.

Mã nguồn: `salary_model.predict_profile`, `salary_model.advise`, `prediction_support.py`, `pages/advisor.py`.
"""),
    code(SETUP),
    md("""
## 1. Không huấn luyện lại khi bấm
Huấn luyện mỗi lần bấm → kết quả có thể khác nhau, chờ lâu. Ứng dụng chỉ nạp mô hình đã lưu: cùng hồ sơ thì hôm nay và ngày mai ra cùng kết quả, và mô hình người dùng dùng chính là mô hình đã được kiểm định.
"""),
    code("""
import time
from career_market.model.advisor import advise, predict_profile
from career_market.model.estimators import MODEL_LABELS

backend = {"role": "Backend Developer", "region": "Hà Nội", "experience_years": 3, "skills": ["Java", "Spring Boot", "SQL"]}
start = time.perf_counter(); result = advise(backend); first = time.perf_counter() - start
start = time.perf_counter(); advise(backend); second = time.perf_counter() - start
print(f"Lần đầu (gồm nạp mô hình): {first:.2f} s · lần hai: {second:.2f} s")
"""),
    md("""
## 2. Hồ sơ đủ dữ liệu: Backend · Hà Nội · 3 năm · Java, Spring Boot, SQL
Ứng dụng hiện **khoảng trước, con số sau** – như dự báo "26–32 độ" thay vì "29,3 độ".
"""),
    code("""
def summary(result):
    m = result["market"]
    return pd.Series({
        "Cấp bậc suy ra": result["level"], "Đủ dữ liệu?": result["supported"], "Số tin cùng vai trò × cấp bậc": result["cohort_rows"],
        "Khoảng lương 80%": f"{result['low']:.1f} – {result['high']:.1f}",
        "Mức điển hình": "—" if result["salary"] is None else round(result["salary"], 1),
        "Trung vị thị trường của vai trò": m["role_median"], "Lý do (nếu ít dữ liệu)": result["support_message"] or "—",
    })

summary(result).to_frame("Backend 3 năm")
"""),
    md("""
## 3. Thuật toán gợi ý kỹ năng
1. Ứng viên kỹ năng: chưa có và xuất hiện ở ≥ 3% số tin cùng vai trò (không gợi ý Figma cho Backend).
2. Bật **đúng một** kỹ năng, dự đoán lại → mức tăng ("nếu tôi giống hệt hiện tại nhưng biết thêm X").
3. Xếp theo mức tăng; thiếu thì bổ sung kỹ năng được yêu cầu nhiều nhất, ghi rõ lý do.

Không xếp theo độ phổ biến vì người dùng hỏi "học gì để tăng lương", không phải "cái gì phổ biến".
"""),
    code("""
recs = pd.DataFrame(result["recommendations"])
display(recs.rename(columns={"skill": "Kỹ năng", "uplift": "Tăng lương (triệu)", "demand_share": "Tỉ lệ tin yêu cầu", "reason": "Lý do"}))
top = result["recommendations"][0]["skill"]
manual = predict_profile({**backend, "skills": backend["skills"] + [top]})["predicted"] - predict_profile(backend)["predicted"]
print(f"Tự kiểm tra {top}: bảng {result['recommendations'][0]['uplift']:+.2f} · tính tay {manual:+.2f}")
charts.recommendation_chart(result["recommendations"]);
"""),
    md("""
## 4. Lộ trình theo kinh nghiệm
"""),
    code("""
display(pd.DataFrame(result["experience_path"]))
charts.experience_path_chart(result["experience_path"]);
"""),
    md("""
Lương tăng chậm trong cấp Middle rồi nhảy khi lên Senior (5 năm) – khớp insight ở trang Tổng quan. Ràng buộc đơn điệu chỉ cấm *giảm*, không cấm đi ngang.

## 5. Hồ sơ ít dữ liệu: chỉ hiện khoảng
"""),
    code("""
data_engineer = {"role": "Data Engineer", "region": "Hà Nội", "experience_years": 3, "skills": ["Python", "SQL", "Spark"]}
low_data = advise(data_engineer)
display(summary(low_data).to_frame("Data Engineer 3 năm"))
pd.DataFrame(low_data["recommendations"])[["skill", "demand_share", "reason"]]
"""),
    md("""
Một người tư vấn trung thực sẽ nói "với vị trí này tôi chỉ biết lương thường trong khoảng X–Y" thay vì bịa một con số. Trang không hiện mức tăng lương của từng kỹ năng cho hồ sơ ít dữ liệu.

## 6. Bảo đảm "thêm kỹ năng không bao giờ làm giảm lương"
"""),
    code("""
from career_market.data.rules import SKILLS

profiles = [
    {"role": "Backend Developer", "region": "Hà Nội", "experience_years": 5, "skills": []},
    {"role": "Kiểm thử (QA/QC)", "region": "TP. Hồ Chí Minh", "experience_years": 1, "skills": ["SQL"]},
]
rows = []
for name in ["GradientBoosting", "Ridge", "RandomForest"]:
    worst = 0.0
    for p in profiles:
        base = predict_profile(p, name)["predicted"]
        for skill in SKILLS:
            if skill not in p["skills"]:
                worst = min(worst, predict_profile({**p, "skills": p["skills"] + [skill]}, name)["predicted"] - base)
    rows.append({"Mô hình": MODEL_LABELS[name], "Thay đổi nhỏ nhất khi thêm 1 kỹ năng (triệu)": round(worst, 4) + 0.0})
pd.DataFrame(rows)
"""),
    md("""
Kiểm thử tự động chạy đúng phép thử này trên mô hình đã lưu để chặn lỗi tái phát khi huấn luyện lại.

## 7. Chia sẻ hồ sơ qua đường dẫn
`/?role=Backend Developer&region=Hà Nội&years=3&skills=Java,Spring Boot,SQL` mở thẳng kết quả. Giá trị không hợp lệ bị bỏ qua thay vì gây lỗi.
"""),
    code("""
from urllib.parse import urlencode
from career_market.data.rules import REGIONS, ROLE_ORDER

def parse_query(q):
    shared = {"role": q.get("role") if q.get("role") in ROLE_ORDER else None,
              "region": q.get("region") if q.get("region") in REGIONS else None,
              "skills": [s for s in q.get("skills", "").split(",") if s in SKILLS]}
    try:
        shared["years"] = min(max(float(q.get("years", "")), 0.0), 20.0)
    except ValueError:
        shared["years"] = None
    return shared

print("http://localhost:8502/?" + urlencode({"role": "Backend Developer", "region": "Hà Nội", "years": 3, "skills": "Java,Spring Boot,SQL"}))
pd.DataFrame([parse_query({"role": "Backend Developer", "years": "3", "skills": "Java,Spring Boot,SQL"}),
              parse_query({"role": "Hacker", "years": "99", "skills": "Java,Excel97"})])
"""),
    md("""
## Kết luận
- Trang tư vấn đáp ứng đủ tiêu chí của user story và nói thật về mức độ chắc chắn: khoảng trước, con số sau; ít dữ liệu thì chỉ có khoảng.
- Lời khuyên luôn hợp lý nhờ ràng buộc đơn điệu.
- ⚠️ Mức tăng là tương quan, không phải lời hứa; lương là lương chào tuyển; mô hình chưa đạt chuẩn production.
"""),
])

print("written", sorted(p.name for p in OUT.glob("tinh_nang_*.ipynb")))
