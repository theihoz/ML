"""Compare original experience with evidenced bounds; export the selected rows."""

import os
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Kinh nghiệm", layout="wide")
st.title("Đối chiếu kinh nghiệm")
st.write(
    "Hai cận tính bằng năm; tháng chia 12. Cận chưa biết để trống. "
    "Thiếu dữ liệu khác với không yêu cầu kinh nghiệm; không tính trung điểm."
)
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
sources = {source.source_id: source for source in service.sources()}
source_id = st.selectbox("Nguồn dữ liệu", list(sources), key="experience_source")
source = sources[source_id]
st.caption(f"{source.platform} · Kaggle v{source.revision} · {source.license}")
status = st.selectbox("Trạng thái", ["Tất cả", "ok", "missing", "review"], key="experience_status")
kind = st.selectbox(
    "Dạng kinh nghiệm",
    [
        "Tất cả",
        "exact",
        "range",
        "greater_than",
        "less_than",
        "at_least",
        "at_most",
        "no_experience",
        "missing",
        "unknown",
    ],
    key="experience_kind",
)
st.caption(
    "greater_than / less_than: trên / dưới; at_least / at_most: từ / tối đa. "
    "review: cần rà soát theo experience_reason, không dùng như số năm hợp lệ."
)
try:
    report = service.experience_report(
        source_id,
        status=None if status == "Tất cả" else status,
        kind=None if kind == "Tất cả" else kind,
    )
except MarketError as error:
    st.error(str(error))
    st.stop()

st.metric("Số dòng nguồn", report["total_count"])
st.metric("Số dòng đang lọc", report["filtered_count"])
if report["rows"]:
    st.dataframe(
        report["rows"],
        hide_index=True,
        column_order=[
            "experience_raw",
            "experience_min",
            "experience_max",
            "experience_kind",
            "experience_status",
            "experience_reason",
            "source_id",
            "job_id",
            "job_url",
        ],
        column_config={"job_url": st.column_config.LinkColumn(display_text="Tin gốc")},
    )
else:
    st.info("Không có dòng phù hợp bộ lọc.")
st.download_button(
    "Tải CSV đang lọc",
    data=report["csv"].encode("utf-8-sig"),
    file_name=f"{source_id}-experience.csv",
    mime="text/csv",
)
with st.expander("Xuất xứ"):
    st.write(source.attribution)
st.info("Số dòng thô trước lọc nghề/khử trùng; ML vẫn bị chặn, không huấn luyện.")
