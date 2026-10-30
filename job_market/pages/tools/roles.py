"""T03: compare raw postings with role evidence and export the visible selection."""

import csv
import io
import json
import os
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Vai trò phần mềm", layout="wide")
st.title("Vai trò phần mềm")
st.write("Đối chiếu chức danh với bảy nhóm nghề, giữ bằng chứng và trường hợp chưa rõ.")
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
source_id = st.selectbox("Nguồn dữ liệu", [source.source_id for source in service.sources()])

try:
    preview = service.preview(source_id, limit=None)
except MarketError as error:
    st.error(str(error))
    st.stop()

st.caption(preview.source.attribution)
if not preview.source.has_job_description:
    st.warning("Thiếu JD: chỉ phân nhóm từ chức danh; không tự điền mô tả hoặc kỹ năng.")
st.info(
    "review: chưa rõ hoặc có nhiều vai trò. out_of_scope: ngoài bảy nhóm nghề. "
    "Đây là số dòng thô, chưa khử trùng; ML vẫn bị chặn."
)

rows = []
for record in preview.records:
    raw = record.raw
    title = raw.get("job_title", raw.get("title", ""))
    description = raw.get("job_description", "")
    requirements = raw.get("job_requirements", "")
    result = service.classify_role(title, description, requirements)
    rows.append(
        {
            "raw_title": title,
            **result,
            "role_evidence": json.dumps(result["role_evidence"], ensure_ascii=False),
            "source_id": record.source_id,
            "source_job_id": record.job_id,
            "source_job_url": record.job_url,
            **raw,
        }
    )

role = st.selectbox(
    "Vai trò",
    ["Tất cả", "Backend", "Frontend", "Fullstack", "Mobile", "Data/ML", "DevOps", "QA Automation"],
    key="role_filter",
)
status = st.selectbox(
    "Trạng thái", ["Tất cả", "matched", "review", "out_of_scope"], key="status_filter"
)
visible = [
    row
    for row in rows
    if (role == "Tất cả" or row["role"] == role)
    and (status == "Tất cả" or row["role_status"] == status)
]
st.metric("Số dòng sau lọc", len(visible))
st.dataframe(visible, hide_index=True)
if not visible:
    st.info("Không có dòng phù hợp với bộ lọc.")

output = io.StringIO(newline="")
columns = (
    list(rows[0]) if rows else ["raw_title", "role", "role_status", "role_evidence", "role_reason"]
)
writer = csv.DictWriter(output, fieldnames=columns)
writer.writeheader()
writer.writerows(visible)
st.download_button(
    "Tải CSV theo bộ lọc",
    data=output.getvalue().encode("utf-8-sig"),
    file_name=f"{source_id}-roles-{role}-{status}.csv",
    mime="text/csv",
)
