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

Trang này cho biết mô hình đã học từ những tin tuyển dụng nào: bắt đầu từ bao nhiêu tin, bỏ đi bao nhiêu và vì sao, rồi chia dữ liệu ra sao.

Mỗi phần đi theo cùng một mạch để dễ theo dõi: **gặp vấn đề gì → để nguyên thì hỏng ở đâu → nhóm chọn cách nào → vì sao → phải đánh đổi gì**.

1. Dữ liệu gốc có những lỗi gì (đếm lại trên file gốc).
2. Phát hiện quan trọng nhất: **2.400 tin do máy sinh ra**, không phải tin thật.
3. Cách đọc các kiểu ghi lương khác nhau, chạy trên ví dụ thật.
4. Lọc dữ liệu và chia dữ liệu **theo công ty**.

> **Từ cần biết:** *tập học (train)* là phần dữ liệu mô hình được xem để học; *tập chọn (valid)* dùng để so và chọn mô hình; *tập kiểm tra (test)* chỉ mở một lần ở cuối để chấm điểm thật. *Trung vị* là giá trị đứng giữa khi xếp từ thấp đến cao.

Chi tiết về cách gán từng nhãn nằm ở notebook `gan_nhan_du_lieu.ipynb`. Mã nguồn: `src/career_market/data/rules.py`, `src/career_market/data/dataset.py`, `pages/dataset.py`.
"""),
    code(SETUP),
    md("""
## 1. Ba nguồn dữ liệu gốc và lỗi của chúng
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
**Khoảng lương giả "1 – 40 triệu".** Đây là giá trị điền sẵn của biểu mẫu đăng tin, không phải mức lương thật. Điểm giữa là 20,5 triệu, trông rất bình thường, nên máy không báo lỗi mà âm thầm học sai. Đây là kiểu lỗi nguy hiểm nhất. Cách xử lý: bỏ mọi khoảng lương mà mức cao gấp hơn 3 lần mức thấp.

## 2. Phát hiện lớn nhất: 2.400 tin do máy sinh ra

**Dấu hiệu đầu tiên:** ở ba trang TopCV, VietnamWorks, CareerViet, ngày đăng tin trải đều từng năm từ 2018 đến 2025. Thị trường thật không bao giờ đều như vậy. Lúc đầu nhóm chỉ nghĩ cột ngày bị hỏng; xem kỹ hơn thì thấy cả nhóm tin này có chung các dấu hiệu dưới đây.
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
- **Vấn đề:** 2.400 tin (đúng 800 tin mỗi trang) có đường dẫn chứa `-hist`, ngày đăng trải đều, danh sách kỹ năng ngẫu nhiên (ví dụ tin Android lại đòi Swift và React) và không có mô tả công việc. Trước khi loại, chúng chiếm 54% số tin có lương.
- **Để nguyên thì sao:** tin giả dễ đoán hơn tin thật, nên điểm của mô hình đẹp một cách giả tạo. Mô hình cũ sai trung bình 16,5% khi chấm trên tập có lẫn tin giả, nhưng 18,0% khi chỉ chấm tin thật. Giống như ôn thi bằng bộ đề do máy bịa ra.
- **Nhóm chọn:** loại hẳn những tin này (thay vì chỉ sửa cột ngày hay đánh dấu).
- **Đánh đổi:** mất hơn nửa dữ liệu; tập kiểm tra cuối chỉ còn 288 tin.

## 3. Đọc lương – mỗi quy tắc đều có lý do

| Cách ghi trong tin | Cách xử lý | Vì sao |
|---|---|---|
| "15 - 25 triệu" | lấy điểm giữa: 20 triệu | Nhà tuyển dụng thường nói "lương khoảng 20 triệu"; mức cao là mức trần |
| "Tới 30 triệu" / "Từ 20 triệu" | đoán đầu còn lại theo **thói quen ghi lương của từng trang** (học từ tin ghi đủ hai đầu) | Mỗi trang ghi khoảng rộng hẹp khác nhau; một hệ số cố định không đúng cho mọi trang |
| Đô la / lương theo năm | đổi theo tỷ giá của năm đó / chia 12 | Tránh "1.000 USD" bị hiểu thành 1.000 triệu |
| Mức cao gấp hơn 3 lần mức thấp | bỏ | Một vị trí hiếm khi chênh nhiều thế; khoảng quá rộng là cách né công bố lương |
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
## 4. Lọc dữ liệu và chia theo công ty

**Vì sao chia theo công ty?** Một công ty thường đăng hàng chục tin gần giống nhau. Nếu chia ngẫu nhiên từng tin, mô hình chỉ cần "nhớ" công ty là đoán đúng, giống như được ôn đúng đề sẽ thi. Nhưng người dùng thật thường hỏi về **công ty mới**, nên tập kiểm tra phải gồm những công ty mô hình chưa từng thấy. Mỗi công ty được xếp vào một tập cố định theo tên (dùng hàm băm), nên chạy lại bao nhiêu lần cũng ra cùng một cách chia.
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
Hai biểu đồ dưới đây giống hệt hai biểu đồ trên trang Dữ liệu huấn luyện.
"""),
    code("""
charts.split_by_role(frame);
"""),
    code("""
charts.salary_distribution(frame);
"""),
    md("""
## Kết luận
- Mỗi lỗi của dữ liệu gốc có một cách xử lý rõ ràng và được kiểm thử tự động.
- Bài học lớn nhất: *nhiều dữ liệu chỉ có ích khi dữ liệu là thật*. Bỏ 2.400 tin giả làm điểm của mô hình kém đi, nhưng là điểm trung thực.
- Chia theo công ty là quyết định quan trọng nhất về cách đánh giá: mọi con số đều đo trên những công ty mô hình chưa từng gặp.
"""),
])

# ───────────────────────────────────────────── 2. TỔNG QUAN
notebook("tinh_nang_2_tong_quan_thi_truong.ipynb", [
    md("""
# Tính năng 2 – Trang **Tổng quan** (bức tranh thị trường)

Trang có 4 thẻ số liệu và 6 biểu đồ mô tả thị trường từ 1.735 tin tuyển dụng thật có ghi lương. Phần này chỉ **mô tả dữ liệu**, không dùng mô hình dự đoán (trừ thẻ "sai số"). Notebook tính lại từng con số, vẽ lại từng biểu đồ, kèm điều rút ra được và lý do chọn loại biểu đồ.

Mã nguồn: `pages/overview.py`, `src/career_market/ui/charts.py`.
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
### Vì sao dùng **trung vị** thay cho trung bình?
Một phòng có 9 người lương 20 triệu và một giám đốc lương 200 triệu: lương trung bình là 38 triệu, nhưng không ai trong 9 người kia nhận gần 38 triệu. Trung vị (20 triệu) mới mô tả đúng "người bình thường" trong phòng.
"""),
    code("""
team = pd.Series([20] * 9 + [200])
print(f"Ví dụ: trung bình {team.mean():.0f} · trung vị {team.median():.0f} triệu")
print(f"Dữ liệu thật: trung bình {frame['salary'].mean():.1f} · trung vị {frame['salary'].median():.1f} · độ lệch phải (skew) {frame['salary'].skew():.2f}")
"""),
    md("""
## 1. Công nghệ được tuyển nhiều – và lương theo công nghệ
Dùng **biểu đồ cột nằm ngang** vì có nhiều kỹ năng và tên khá dài. Trang web hiện toàn bộ kỹ năng; ở đây chỉ vẽ 15 kỹ năng đầu cho gọn.
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
**Điều rút ra:** kỹ năng được tuyển nhiều nhất (Java, React, SQL) không phải kỹ năng trả cao nhất (AWS, LLM/GenAI, Next.js). Đây mới chỉ là quan sát: tin đòi AWS có thể đơn giản là tin tuyển người nhiều kinh nghiệm. Mô hình ở tính năng 4 mới tách được hai yếu tố này.

## 2. Kinh nghiệm và thu nhập
Dùng **biểu đồ hộp theo số năm kinh nghiệm**, cộng một đường nối các trung vị, để thấy cả xu hướng lẫn độ chênh giữa các tin. Mức độ liên quan đo bằng **hệ số Spearman** (chỉ xét thứ tự cao/thấp), vì lương không tăng theo đường thẳng và có vài tin lương rất cao.
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
Lương nhảy mạnh nhất giữa **4 và 5 năm** (từ Middle lên Senior): lên Senior là đổi vai trò, không chỉ thêm một năm làm việc.

## 3. Khu vực
"""),
    code("""
regions = frame.groupby("region")["salary"].agg(["size", "median"]).sort_values("size", ascending=False)
regions["Tỉ lệ tin"] = (regions["size"] / len(frame) * 100).round(1).astype(str) + "%"
display(regions.rename(columns={"size": "Số tin", "median": "Trung vị"}))
charts.region_salary(frame);
"""),
    md("""
⚠️ Không nên kết luận "TP. Hồ Chí Minh lương thấp hơn": công ty ở TP. Hồ Chí Minh hay ghi "Thương lượng", nên số tin có lương ít và có thể không đại diện.

## 4. Vai trò, và vai trò theo từng khu vực
**Bản đồ nhiệt** (ô càng đậm, lương càng cao) cho bảng hai chiều vai trò × khu vực. Ô có dưới 3 tin được để trống có chủ đích, vì quá ít để tin.
"""),
    code("""
charts.role_salary(frame);
"""),
    code("""
charts.role_region_heatmap(frame);
"""),
    md("""
## Kết luận
1. Kinh nghiệm là yếu tố ảnh hưởng mạnh nhất; bước nhảy lớn nhất là khi lên Senior.
2. Data Engineer, DevOps, quản lý kỹ thuật được trả cao hơn rõ so với lập trình phổ thông (nhưng vài nhóm có rất ít tin).
3. Kỹ năng được tuyển nhiều chưa chắc là kỹ năng trả cao.
4. So sánh giữa các khu vực luôn phải kèm cảnh báo về việc nhiều công ty không ghi lương.
"""),
])

# ───────────────────────────────────────────── 3. THỊ TRƯỜNG
notebook("tinh_nang_3_thi_truong_viec_lam.ipynb", [
    md("""
# Tính năng 3 – Trang **Thị trường việc làm**

Trang cho phép lọc tin tuyển dụng có ghi lương theo **nguồn đăng tin**, **vai trò** và **khu vực**, rồi xem kỹ năng nào được tuyển nhiều nhất và kỹ năng nào đi kèm lương cao. Trang chỉ mô tả dữ liệu, không dùng mô hình dự đoán.

Dữ liệu là 1.735 tin thật, giống trang Tổng quan. Bộ lọc biến bức tranh chung thành câu trả lời riêng cho từng nghề, từng nơi.

Mã nguồn: `pages/market.py`, `src/career_market/ui/cache.py` (hàm `filter_postings`), `src/career_market/ui/charts.py`.
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
Quy ước: để trống bộ lọc nghĩa là lấy tất cả; mỗi tin chỉ được đếm một lần.
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
Thanh màu xám là kỹ năng có dưới 10 tin trong phần đã lọc: quá ít dữ liệu, chưa nên kết luận.
"""),
    code("""
charts.top_skill_salary(view, limit=20, min_postings=10)
"""),
    md("""
⚠️ Nguồn TopCV 2026 **chỉ có chức danh**, không có mô tả công việc, nên kỹ năng được đoán từ tiêu đề tin. Vì vậy "ít tin có kỹ năng" không có nghĩa là các tin đó không đòi kỹ năng.

## Kết luận
- Bộ lọc biến bức tranh chung thành câu trả lời riêng cho từng nghề, từng nơi.
- Kỹ năng được tuyển nhiều chưa chắc là kỹ năng trả cao.
- Lương đi kèm một kỹ năng chỉ cho thấy hai thứ hay xuất hiện cùng nhau, chưa chứng minh học kỹ năng đó sẽ được tăng lương.
"""),
])

# ───────────────────────────────────────────── 4. MÔ HÌNH
notebook("tinh_nang_4_danh_gia_mo_hinh.ipynb", [
    md("""
# Tính năng 4 – Trang **Đánh giá mô hình** (phần 1: huấn luyện và so sánh)

Notebook trả lời: mô hình nào được chọn và vì sao, đoán sai bao nhiêu, đoán sai ở đâu, yếu tố nào quyết định lương, và kỹ năng nào đáng học. Phần độ tin cậy và chuẩn đưa vào sử dụng nằm ở notebook tính năng 5.

> **Từ cần biết:** *tập học (train)* là phần dữ liệu mô hình được xem để học; *tập chọn (valid)* dùng để so và chọn mô hình; *tập kiểm tra (test)* chỉ mở một lần ở cuối để chấm điểm thật. *Trung vị* là giá trị đứng giữa khi xếp từ thấp đến cao. *MAE* là trung bình mô hình đoán lệch bao nhiêu triệu đồng mỗi tin.

Mã nguồn: `src/career_market/model/estimators.py`, `src/career_market/model/training.py`, `pages/evaluation.py`.
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
## 1. Mô hình được xem gì – và cố ý **không** được xem gì
Mô hình được xem: vai trò, khu vực, cấp bậc, **trang đăng tin, hình thức làm việc, loại công ty**, số năm kinh nghiệm, năm của tin, 4 dấu hiệu từ chức danh (chuyên gia, trưởng…) và danh sách kỹ năng.

Mô hình **không** được xem tên công ty, tiêu đề gốc hay chuỗi lương. Nếu biết tên công ty, mô hình sẽ học kiểu "công ty X trả cao", và điều đó vô dụng khi người dùng hỏi về một công ty mới.
"""),
    code("""
X = feature_frame(parts["train"])
print("Số cột đầu vào trước khi mã hóa:", X.shape[1])
X.iloc[:3, :12]
"""),
    md("""
## 2. Bốn ứng viên – như bốn cách con người ước lượng lương

| Mô hình | Giống như ngoài đời | Điểm yếu |
|---|---|---|
| **Mốc trung vị** | Ai hỏi cũng trả lời "khoảng 25 triệu" | Chỉ là mức tối thiểu để so |
| **Ridge** | Một bảng cộng điểm: Backend +2, mỗi năm kinh nghiệm +3, biết AWS +1 | Không hiểu "còn tùy hoàn cảnh" |
| **Random Forest** | Hỏi 300 chuyên viên, mỗi người xem một phần hồ sơ, rồi lấy trung bình | Từng người dễ "học thuộc" ví dụ đã thấy |
| **Gradient Boosting** | Một hội đồng làm nối tiếp: người sau chỉ sửa chỗ người trước đoán sai | Khó giải thích hơn Ridge |

**Ba nguyên tắc khi huấn luyện:**
- Học trên *tỉ lệ* chứ không phải số tuyệt đối: lệch 5 triệu với người lương 10 triệu nghiêm trọng hơn nhiều so với người lương 100 triệu.
- Chọn mô hình bằng sai số trên **tập chọn**, và chốt cách chọn từ trước.
- **Tập kiểm tra cuối** chỉ mở một lần để chấm, không dùng để chọn.
"""),
    code("""
y = parts["train"]["salary"]
print(f"Skew của lương: {y.skew():.2f} → sau logarit: {np.log(y).skew():.2f}")
rows = [{"Mô hình": MODEL_LABELS[n], "Siêu tham số": t["params"], "MAE valid": t["valid_MAE"]} for n, trials in report["tuning"].items() for t in trials]
tuning = pd.DataFrame(rows)
tuning.assign(**{"Chọn": np.where(tuning.groupby("Mô hình")["MAE valid"].transform("min") == tuning["MAE valid"], "✓", "")})
"""),
    md("""
## 3. Quy tắc đời thường: thêm kinh nghiệm hay kỹ năng không thể làm giảm lương

**Vấn đề:** thêm kỹ năng Java vào hồ sơ Backend 5 năm từng làm lương dự đoán *giảm* từ 47,7 xuống 42,3 triệu. Mô hình không bị lỗi lập trình mà học đúng dữ liệu: cột kỹ năng ghi những gì **tin tuyển dụng yêu cầu**, và tin liệt kê nhiều kỹ năng thường là tin tuyển người mới hoặc tuyển hàng loạt, lương thấp. Bảng dưới kiểm tra điều đó trên dữ liệu hiện tại:
"""),
    code("""
backend = frame[frame["role"] == "Backend Developer"]
bins = pd.cut(backend["skill_count"], [-1, 0, 2, 4, 6, 30], labels=["0", "1–2", "3–4", "5–6", "7+"])
backend.groupby(bins, observed=False)["salary"].agg(["size", "median"]).rename(columns={"size": "Số tin", "median": "Trung vị lương"}).T
"""),
    md("""
**Cách xử lý:** bỏ hẳn thông tin "số lượng kỹ năng", và buộc cả ba mô hình tuân theo quy tắc "thêm kỹ năng hoặc kinh nghiệm thì lương không giảm" (mỗi mô hình một cách kỹ thuật riêng). Kiểm tra trên mô hình đã lưu:
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
## 4. Chạy lại để kiểm chứng: huấn luyện lại Gradient Boosting với thiết lập đã chọn
"""),
    code("""
params = report["models"]["GradientBoosting"]["params"]
model = build_model("GradientBoosting", **params).fit(feature_frame(parts["train"]), parts["train"]["salary"])
again = {s: scores(parts[s]["salary"], model.predict(feature_frame(parts[s])))["MAE"] for s in ["train", "valid", "test"]}
pd.DataFrame({"Fit lại trong notebook": again, "Trong metrics.json": {s: report["models"]["GradientBoosting"][s]["MAE"] for s in again}})
"""),
    md("""
## 5. Kết quả trên ba tập dữ liệu
"""),
    code("""
rows = [{"Mô hình": v["label"], "MAE train": v["train"]["MAE"], "MAE valid": v["valid"]["MAE"], "MAE test": v["test"]["MAE"],
         "RMSE test": v["test"]["RMSE"], "R² test": v["test"]["R2"], "MAPE test %": v["test"]["MAPE"]} for v in report["models"].values()]
display(pd.DataFrame(rows).set_index("Mô hình"))
print("Được chọn theo MAE valid:", MODEL_LABELS[report["selected"]])
charts.model_comparison(report);
"""),
    md("""
- Gradient Boosting sai ít nhất trên tập chọn nên được chọn **trước khi mở tập kiểm tra**; trên tập kiểm tra nó vẫn tốt nhất.
- Gradient Boosting đoán tốt hơn hẳn trên tập học so với tập chọn: với khoảng 1.200 tin để học, mô hình đã "học thuộc" một phần.
- Sai số cao hơn bản trước kia có lẫn tin do máy sinh (5,82 triệu), vì tin thật khó đoán hơn. Hai con số này không so trực tiếp được.

## 6. Mô hình đoán sai nhiều ở đâu?
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
Sai nhiều nhất ở Tech Lead/Architect và vị trí quản lý: cùng chức danh nhưng lương ở một startup 20 người khác xa một tập đoàn 5.000 người, mà dữ liệu không có thông tin quy mô công ty.

## 7. Yếu tố quyết định lương và kỹ năng đáng học
**Cách đo mức quan trọng:** xáo trộn một cột thông tin rồi xem mô hình đoán kém đi bao nhiêu. Giống như cho một cầu thủ nghỉ một trận để biết anh ấy quan trọng với đội thế nào.
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
⚠️ Mức tăng lương ở đây là phép thử "nếu như" trên một mô hình học từ tin tuyển dụng. Nó cho thấy hai thứ hay đi cùng nhau, **chưa chứng minh** học kỹ năng đó sẽ được tăng lương.
"""),
])

# ───────────────────────────────────────────── 5. KIỂM ĐỊNH & CHUẨN PRODUCTION
notebook("tinh_nang_5_kiem_dinh_va_chuan_production.ipynb", [
    md("""
# Tính năng 5 – Trang **Đánh giá mô hình** (phần 2: có tin được không?)

Một con số sai số trung bình không trả lời được bốn câu hỏi sau:
1. **Khoảng lương có đáng tin?** Nói "80% khả năng" thì có đúng khoảng 80% không?
2. **Thắng thật hay nhờ may?** Mô hình được chọn có tốt hơn thật không, hay chỉ gặp may với bộ dữ liệu kiểm tra?
3. **Có công bằng không?** Mô hình có đoán lệch đều cho một nhóm người nào không? Còn giới tính thì sao?
4. **Đủ tốt để dùng thật chưa?** So với chuẩn mà các trang lương lớn công bố.

Mã nguồn: `src/career_market/model/validation.py`, `model/production.py`, `model/support.py`, `model/promotion.py`.
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
## 1. Khoảng lương có đáng tin? – giống "dự báo 80% khả năng mưa"
Nếu đài dự báo "80% khả năng mưa" cho 100 ngày, một đài tốt phải có khoảng 80 ngày mưa thật. Tương tự, khoảng 80% của ứng dụng phải chứa lương thật của khoảng 80% tin. Khoảng được dựng từ tập chọn và kiểm tra trên tập kiểm tra chưa dùng. Khoảng được tính theo **tỉ lệ** (ví dụ từ 0,8 đến 1,3 lần dự đoán) chứ không cộng trừ một số cố định, vì người lương 80 triệu thường lệch nhiều tiền hơn người lương 15 triệu.
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
Nhìn chung khoảng **hơi rộng hơn cần thiết** (tức là thận trọng), nhưng ở nhóm lương cao chỉ đúng khoảng 71%.

## 2. Thắng thật hay nhờ may? – "thi lại 1.000 lần với đề khác"
Bốc ngẫu nhiên lại các **công ty** trong tập kiểm tra (có thể bốc trùng) để tạo một "đề thi" mới, chấm lại, và lặp 1.000 lần. Bốc theo công ty chứ không theo từng tin, vì các tin của cùng một công ty rất giống nhau. Các mô hình luôn được so **trên cùng một đề**.
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
Gradient Boosting thắng Ridge và Random Forest ở khoảng 83–91% số đề, nhưng khoảng chênh lệch 95% **vẫn chứa số 0**. Nghĩa là với 288 tin thật, **chưa đủ bằng chứng** để nói nó tốt hơn hẳn. (Trên dữ liệu cũ có lẫn tin giả, con số này là 100%, đẹp một cách giả tạo.) So với "mốc trung vị" thì thắng chắc chắn.

## 3. Có công bằng không?
Một chiếc cân lệch 1 kg với tất cả mọi người thì vẫn "công bằng"; chỉ lệch với người thấp mới là thiên vị. Độ lệch của một nhóm = trung bình (dự đoán − thật) / thật. Nếu khoảng tin cậy chứa số 0 thì chưa có bằng chứng lệch; nhóm dưới 20 tin chỉ được báo cáo, không kết luận.
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
**Junior bị đoán cao khoảng 7%** (và khoảng tin cậy không chứa 0): người mới đi làm nên trừ hao kết quả. **Giới tính không đo được**, vì dữ liệu không có thông tin này; nói "mô hình công bằng về giới" là không trung thực. Riêng việc tin tuyển dụng ghi điều kiện giới tính là dấu hiệu phân biệt đối xử theo Bộ luật Lao động 2019.

## 4. Đủ tốt để dùng thật chưa? – theo chuẩn Glassdoor, LinkedIn công bố
Ba chỉ số dễ hiểu:
- **trung vị sai số %**: một nửa số dự đoán lệch ít hơn mức này;
- **tỉ lệ dự đoán lệch không quá 20%**;
- **khoảng 80% có chứa lương thật đúng khoảng 80% số lần không**.

Để không "đậu nhờ may", mức chung được chấm theo kết quả **xấu nhất hợp lý** của 1.000 lần thi lại; mức theo từng nhóm chấm theo giá trị đo được.
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
**Mô hình chưa đạt chuẩn.** Vì vậy ứng dụng:
1. ghi rõ "kết quả mang tính tham khảo";
2. chỉ hiện **con số** khi nhóm vai trò × cấp bậc có ít nhất 20 tin để học và không trượt chuẩn; còn lại chỉ hiện một **khoảng lương rộng hơn**;
3. khi huấn luyện lại, mô hình mới chỉ được thay mô hình cũ nếu qua **cổng kiểm tra**: đạt chuẩn, hoặc cả hai cùng chưa đạt nhưng mô hình mới không kém hơn ở chỉ số chung nào và tốt hơn ở ít nhất một điểm.
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

Yêu cầu của người dùng: *"Tôi muốn nhập kỹ năng và kinh nghiệm của mình; phần mềm dựa vào mô hình đã huấn luyện sẵn sẽ dự đoán mức lương và tư vấn kỹ năng nên học thêm."*

Người dùng nhập vai trò, khu vực, số năm kinh nghiệm, kỹ năng (và nếu muốn: chức danh, loại công ty, hình thức làm việc). Kết quả gồm:
- **khoảng lương** thường gặp và **mức điển hình** (nếu đủ dữ liệu), quy về lương gross thị trường gần đúng;
- tối đa **5 kỹ năng nên học**;
- **lộ trình lương** khi có thêm kinh nghiệm.

Mã nguồn: `src/career_market/model/advisor.py`, `model/support.py`, `pages/advisor.py`.
"""),
    code(SETUP),
    md("""
## 1. Không huấn luyện lại khi người dùng bấm nút
Nếu huấn luyện lại mỗi lần bấm, người dùng phải chờ lâu và kết quả có thể mỗi lần một khác. Ứng dụng chỉ nạp mô hình đã lưu: cùng một hồ sơ thì hôm nay hay ngày mai đều ra cùng kết quả, và mô hình người dùng đang dùng chính là mô hình đã được kiểm định.
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
Ứng dụng hiện **khoảng lương trước, con số sau**, giống dự báo thời tiết "26–32 độ" thay vì "29,3 độ". Khoảng ở đây chứa một nửa số tin tương tự (từ mức 25% đến mức 75%).
"""),
    code("""
def summary(result):
    m = result["market"]
    return pd.Series({
        "Cấp bậc suy ra": result["level"], "Đủ dữ liệu?": result["supported"], "Số tin cùng vai trò × cấp bậc": result["cohort_rows"],
        "Khoảng lương (gross gần đúng)": f"{result['low']:.1f} – {result['high']:.1f}",
        "Mức điển hình": "—" if result["salary"] is None else round(result["salary"], 1),
        "Trung vị thị trường của vai trò": m["role_median"], "Lý do (nếu ít dữ liệu)": result["support_message"] or "—",
    })

summary(result).to_frame("Backend 3 năm")
"""),
    md("""
## 3. Cách chọn kỹ năng để gợi ý
1. Chỉ xét kỹ năng người dùng chưa có và xuất hiện ở ít nhất 3% số tin cùng vai trò (không gợi ý Figma cho lập trình viên Backend).
2. Thêm **đúng một** kỹ năng vào hồ sơ rồi dự đoán lại, để biết lương thay đổi bao nhiêu ("nếu tôi giữ nguyên mọi thứ nhưng biết thêm X").
3. Xếp theo mức tăng lương; nếu chưa đủ 5 kỹ năng thì bổ sung kỹ năng được tuyển nhiều nhất, có ghi rõ lý do.

Không xếp theo độ phổ biến, vì người dùng hỏi "học gì để tăng lương", không phải "cái gì đang phổ biến".
"""),
    code("""
recs = pd.DataFrame(result["recommendations"])
display(recs.rename(columns={"skill": "Kỹ năng", "uplift": "Tăng lương (triệu)", "demand_share": "Tỉ lệ tin yêu cầu", "reason": "Lý do"}))
top = result["recommendations"][0]["skill"]
manual = advise({**backend, "skills": backend["skills"] + [top]})["salary_range"]["median"] - result["salary_range"]["median"]
print(f"Tự kiểm tra {top}: bảng {result['recommendations'][0]['uplift']:+.2f} · tính tay {manual:+.2f}")
charts.recommendation_chart(result["recommendations"]);
"""),
    md("""
## 4. Lộ trình lương theo kinh nghiệm
"""),
    code("""
display(pd.DataFrame(result["experience_path"]))
charts.experience_path_chart(result["experience_path"]);
"""),
    md("""
Lương tăng chậm trong giai đoạn Middle rồi nhảy lên khi đến Senior (khoảng 5 năm), khớp với điều thấy ở trang Tổng quan. Quy tắc "không giảm" chỉ cấm lương đi xuống, không cấm đi ngang.

## 5. Hồ sơ ít dữ liệu: chỉ hiện khoảng lương
"""),
    code("""
data_engineer = {"role": "Data Engineer", "region": "Hà Nội", "experience_years": 3, "skills": ["Python", "SQL", "Spark"]}
low_data = advise(data_engineer)
display(summary(low_data).to_frame("Data Engineer 3 năm"))
pd.DataFrame(low_data["recommendations"])[["skill", "demand_share", "reason"]]
"""),
    md("""
Một người tư vấn trung thực sẽ nói "với vị trí này tôi chỉ biết lương thường nằm trong khoảng X đến Y" thay vì bịa ra một con số. Với hồ sơ ít dữ liệu, trang cũng không hiện mức tăng lương của từng kỹ năng.

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
Bộ kiểm thử tự động chạy đúng phép thử này trên mô hình đã lưu, để lỗi không quay lại sau mỗi lần huấn luyện lại.

## 7. Chia sẻ hồ sơ bằng đường dẫn
Đường dẫn `/?role=Backend Developer&region=Hà Nội&years=3&skills=Java,Spring Boot,SQL` mở thẳng kết quả. Giá trị không hợp lệ được bỏ qua thay vì làm trang báo lỗi.
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
- Trang tư vấn đáp ứng đủ yêu cầu của người dùng và nói thật về mức độ chắc chắn: khoảng trước, con số sau; ít dữ liệu thì chỉ có khoảng.
- Lời khuyên luôn hợp lý nhờ quy tắc "thêm kỹ năng không làm giảm lương".
- ⚠️ Mức tăng lương là quan hệ quan sát được, không phải lời hứa; lương là lương gross thị trường **gần đúng**, được hiệu chỉnh từ lương ghi trên tin tuyển dụng; mô hình chưa đạt chuẩn đưa vào sử dụng.
"""),
])

print("written", sorted(p.name for p in OUT.glob("tinh_nang_*.ipynb")))
