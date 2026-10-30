"""Company audit adapter; parent label overlays may supply prepared session rows."""

import os
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService
from career_market.dashboard import prepared_report

st.set_page_config(page_title="Đối chiếu công ty", layout="wide")
st.title("Đối chiếu công ty và nhóm giữ cùng tập")
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
try:
    # The parent can hand over prepared ML01 rows without reloading or training.
    rows = st.session_state.get("company_prepared_rows")
    if rows is None:
        rows = prepared_report(service)["rows"]
    report = service.company_report(rows)
except MarketError as error:
    st.error(str(error))
    st.stop()

st.subheader("Toàn bộ dữ liệu đã chuẩn bị")
st.caption(
    "Các số tổng gồm cả dòng chưa có nhãn lương, review và ngoài phạm vi nghề; không thể dùng số công ty tổng để mở huấn luyện."
)
for column, key, label in zip(
    st.columns(5),
    ["rows", "entities", "companies", "groups", "review_groups"],
    ["Dòng nguồn", "Entity", "Công ty chuẩn", "Nhóm", "Nhóm cần review"],
):
    column.metric(label, report["summary"][key])
st.info(
    "Chia theo công ty, mục tiêu 70/15/15, seed 42. Cả nhóm phải cùng một tập; nhóm review được cách ly. Đây là báo cáo danh tính, chưa chia tập hoặc huấn luyện; ML06 còn chờ policy hỗ trợ."
)
st.subheader("Chỉ cohort có nhãn lương và danh tính dùng được")
readiness = report["split_readiness"]
for column, key, label in zip(
    st.columns(3),
    ["usable_labeled_entities", "labeled_company_count", "labeled_split_group_count"],
    ["Entity có nhãn dùng được", "Công ty có nhãn dùng được", "Nhóm độc lập có nhãn dùng được"],
):
    column.metric(label, readiness[key])
st.warning(readiness["reason"])
st.caption(
    "Chỉ thống nhất khoảng trắng, hoa/thường và Unicode tương đương. Không suy công ty mẹ/con hoặc recruiter/client; chưa xử lý mọi near-duplicate. Giữ tên/ID nguồn để kiểm toán."
)
st.subheader("Alias công ty và xuất xứ")
st.dataframe(report["aliases"], hide_index=True)
st.subheader("Nhóm không được cắt")
st.dataframe(report["groups"], hide_index=True)
st.subheader("Dòng bằng chứng và lý do review")
st.dataframe(report["rows"], hide_index=True)
st.subheader("Liên kết công ty, tin trùng và đăng lại")
st.dataframe(report["links"], hide_index=True)
for label, key, filename in [
    ("Tải dòng bằng chứng CSV", "csv", "company-rows.csv"),
    ("Tải alias CSV", "aliases_csv", "company-aliases.csv"),
    ("Tải nhóm CSV", "groups_csv", "company-groups.csv"),
    ("Tải liên kết CSV", "links_csv", "company-links.csv"),
]:
    st.download_button(label, report[key], filename, "text/csv")
