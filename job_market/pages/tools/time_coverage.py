import os
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService
from career_market.dashboard import prepared_report

st.set_page_config(page_title="Độ phủ thời gian", layout="wide")
st.title("Độ phủ dữ liệu theo thời gian")
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
try:
    prepared = prepared_report(service)
except MarketError as error:
    st.error(str(error))
    st.stop()
report = service.time_coverage(prepared["rows"])
st.warning(report["reason"])
st.subheader("Phạm vi ngày đăng của từng nguồn")
st.dataframe(report["coverage"], hide_index=True)
st.subheader("Phân bố tháng đăng trong các bản chụp")
st.caption(
    "Bảng mô tả tập tin đã thu thập, không phải tốc độ tăng/giảm nhu cầu thị trường. Giữ riêng từng nguồn; không nối 2023 với 2026 thành một đường xu hướng."
)
st.dataframe(report["periods"], hide_index=True)
st.download_button("Tải bảng độ phủ CSV", report["csv"], "time-coverage.csv", "text/csv")
st.download_button(
    "Tải phân bố tháng CSV", report["periods_csv"], "observed-months.csv", "text/csv"
)
