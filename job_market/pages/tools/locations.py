"""T05: inspect exact location aliases, raw evidence, and the filtered CSV."""

import os
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Địa điểm", layout="wide")
st.title("Địa điểm — đối chiếu raw và nhãn chuẩn")
st.write("Gom các cách viết HCM/HN đã xác minh; giữ nguyên nhãn tỉnh khác theo nguồn.")
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
sources = service.sources()
source_id = st.selectbox(
    "Nguồn dữ liệu", [source.source_id for source in sources], key="location_source"
)
source = next(source for source in sources if source.source_id == source_id)
st.caption(f"{source.platform} · Kaggle v{source.revision} · {source.license}")
st.caption(source.attribution)
st.info(
    "Hậu tố (mới) được giữ trong raw và bằng chứng alias. Chuẩn hóa HCM/HN không xác nhận "
    "cùng phạm vi địa giới qua năm. Hai nguồn có phạm vi khác nhau; chưa đủ căn cứ so sánh "
    "tỉnh/thành hoặc suy ra xu hướng thị trường theo năm."
)

try:
    report = service.location_report(source_id)
    location = st.selectbox(
        "Nhãn địa điểm chuẩn",
        [None, *report["location_options"]],
        format_func=lambda value: "Tất cả" if value is None else value,
        key="canonical_location",
    )
    status = st.selectbox(
        "Trạng thái địa điểm",
        [None, "normalized", "review", "missing"],
        format_func=lambda value: "Tất cả" if value is None else value,
        key="location_status",
    )
    multiple = st.multiselect("Thêm địa điểm (khớp ít nhất một)", report["location_options"])
    work_mode = st.selectbox(
        "Hình thức làm việc", [None, "Remote"], format_func=lambda v: v or "Tất cả"
    )
    if location is not None or status is not None or multiple or work_mode:
        report = service.location_report(
            source_id, location=location, status=status, locations=multiple, work_mode=work_mode
        )
except MarketError as error:
    st.error(str(error))
    st.stop()

st.metric("Số dòng thô của nguồn", report["raw_row_count"])
st.metric("Tin duy nhất sau lọc", report["unique_posting_count"])
st.caption(
    "Remote là hình thức làm việc, độc lập với tỉnh/thành. Nhóm địa điểm có thể chồng lắp; tổng tin đếm một lần theo ID/URL chuẩn."
)
st.caption(
    f"Đang hiển thị {len(report['rows'])} dòng thô sau lọc. Tần suất alias là số dòng gốc, "
    "chưa lọc vai trò hoặc khử trùng, không phải số tin duy nhất hay nhu cầu thị trường."
)
st.subheader("Bảng alias — tần suất chuỗi gốc")
st.dataframe(
    report["alias_table"],
    hide_index=True,
    column_order=[
        "location_raw",
        "locations",
        "raw_rows",
        "location_status",
        "location_aliases",
        "location_unresolved",
        "location_reason",
        "work_modes",
    ],
)
st.subheader("Đối chiếu theo dòng nguồn")
st.dataframe(
    report["rows"],
    hide_index=True,
    column_order=[
        "location_raw",
        "locations",
        "location_status",
        "location_aliases",
        "location_unresolved",
        "location_reason",
        "source_id",
        "job_id",
        "job_url",
        "work_modes",
    ],
)
if not report["rows"]:
    st.info("Không có dòng khớp bộ lọc; CSV vẫn giữ tên cột để đối chiếu.")
st.download_button(
    "Tải CSV raw–chuẩn đang lọc",
    data=report["csv"].encode("utf-8-sig"),
    file_name=f"{source_id}-locations.csv",
    mime="text/csv",
)
