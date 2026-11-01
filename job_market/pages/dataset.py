"""Bộ dữ liệu huấn luyện salary-v2: phễu làm sạch, nhãn train/valid/test và mẫu dữ liệu."""

import json

import streamlit as st

from career_market import salary_app
from career_market.salary_dataset import dataset_path

st.title("Dữ liệu huấn luyện")
frame = salary_app.dataset()
summary = json.loads(dataset_path().with_suffix(".json").read_text(encoding="utf-8"))
funnel = summary["funnel"]
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
    st.image(salary_app.chart("split"), width="stretch")
with right, st.container(border=True):
    st.subheader("Phân bố lương")
    st.caption("Đường đứt: trung vị")
    st.image(salary_app.chart("distribution"), width="stretch")
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
