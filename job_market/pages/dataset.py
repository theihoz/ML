"""Trang Dữ liệu huấn luyện.

Mục này làm gì: phễu làm sạch (tin thô → tin có nhãn), phân bố train/valid/test, bảng dữ liệu + tải CSV.
"""

import json

import streamlit as st

from career_market.model.versions import freshness_line
from career_market.paths import dataset_path
from career_market.ui import cache

st.title("Dữ liệu huấn luyện")
st.caption(freshness_line())
frame = cache.dataset()
summary = json.loads(dataset_path().with_suffix(".json").read_text(encoding="utf-8"))
funnel = summary["funnel"]
# Mục này: phễu làm sạch — mỗi bước loại bớt tin không dùng được.
a, b, c, d = st.columns(4)
a.metric("Tin thô đọc vào", f"{funnel['raw']:,}")
b.metric("Có lương đọc được", f"{funnel['has_salary']:,}")
c.metric("Thuộc vai trò CNTT", f"{funnel['it_role']:,}")
d.metric("Sau khử trùng lặp", f"{funnel['deduplicated']:,}")
st.caption(
    "Nguồn: TopCV 2026, Vietnam IT Job Posts 2026 (VietnamWorks, TopCV, ITviec, CareerViet) "
    "và CareerBuilder 2023 nhóm CNTT. Lương chuẩn hóa về trung điểm khoảng, triệu VND/tháng."
)
left, right = st.columns(2, gap="medium")
with left, st.container(border=True):
    st.subheader("Nhãn train / valid / test theo vai trò")
    st.caption("Chia 70/15/15 theo công ty bằng hash cố định (seed 42)")
    st.image(cache.chart("split"), width="stretch")
with right, st.container(border=True):
    st.subheader("Phân bố lương")
    st.caption("Đường đứt: trung vị")
    st.image(cache.chart("distribution"), width="stretch")
# Mục này: xem và tải bảng dữ liệu theo tập.
split = st.segmented_control(
    "Tập dữ liệu",
    ["train", "valid", "test"],
    selection_mode="multi",
    default=["train", "valid", "test"],
    key="dataset_split",
)
view = frame[frame["split"].isin(split or [])]
st.dataframe(
    view[
        ["row_id", "split", "source", "title", "role", "region", "level"]
        + ["experience_years", "skills", "salary_text", "salary"]
    ],
    hide_index=True,
    width="stretch",
)
st.download_button(
    "Tải bộ dữ liệu CSV",
    view.to_csv(index=False),
    "salary_dataset_v2.csv",
    "text/csv",
    icon=":material/download:",
)
