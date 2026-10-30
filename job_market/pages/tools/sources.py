"""Streamlit entrypoint: only display data returned by MarketService."""

import os
from dataclasses import asdict
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Nguồn tin tuyển dụng", layout="wide")
st.title("Nguồn tin tuyển dụng")
st.write("Xem dữ liệu gốc và xuất xứ của hai nguồn mới được duyệt cho đợt EDA.")
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
source_id = st.selectbox("Nguồn dữ liệu", [source.source_id for source in service.sources()])

try:
    preview = service.preview(source_id)
except MarketError as error:
    st.error(str(error))
    st.stop()

source = preview.source
st.caption(f"{source.platform} · Kaggle v{source.revision} · {source.license}")
st.metric("Số dòng thô", preview.row_count)
st.write(f"Schema: {len(preview.columns)} cột — " + ", ".join(preview.columns))
st.dataframe([record.raw for record in preview.records], hide_index=True)
with st.expander("Xuất xứ và đối chiếu raw"):
    st.write(source.attribution)
    st.link_button("Metadata Kaggle", source.metadata_url)
    st.json(asdict(source))
    st.code(f"SHA-256 raw: {preview.raw_sha256}", language=None)

if not source.has_job_description:
    st.warning("Thiếu JD: nguồn 2026 chỉ có tiêu đề, không tự điền mô tả hoặc kỹ năng.")
st.info(
    "Hai nguồn EDA này chưa tạo thành tập lương đủ huấn luyện. Mô hình demo dùng nguồn lương riêng."
)
st.write(
    "Đây là số dòng thô, chưa lọc vai trò hoặc khử trùng. Hai nguồn có phạm vi khác nhau, "
    "chưa đủ căn cứ để kết luận xu hướng toàn thị trường theo năm."
)
