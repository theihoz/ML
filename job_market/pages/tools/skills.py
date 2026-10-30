"""T07: view and export explicit language evidence from approved new sources."""

import csv
import io
import json
import os
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Ngôn ngữ lập trình", layout="wide")
st.title("Ngôn ngữ lập trình và công nghệ")
st.write("Mỗi tin giữ một danh sách ngôn ngữ và bằng chứng riêng từ tiêu đề, JD, yêu cầu.")
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
source_id = st.selectbox("Nguồn dữ liệu", [source.source_id for source in service.sources()])
try:
    preview = service.preview(source_id, limit=None)
except MarketError as error:
    st.error(str(error))
    st.stop()

if not preview.source.has_job_description:
    st.warning("Thiếu JD: nguồn này chỉ có tiêu đề; không tự điền mô tả hoặc kỹ năng.")

postings = []
for record in preview.records:
    raw = record.raw
    title = raw.get("job_title", raw.get("title", ""))
    description = raw.get("job_description", "")
    requirements = raw.get("job_requirements", "")
    result = service.extract_skills(title, description, requirements)
    postings.append(
        {
            "source_id": record.source_id,
            "job_id": record.job_id or "",
            "job_url": record.job_url,
            "title": title,
            "description": description,
            "requirements": requirements,
            **result,
        }
    )

languages = sorted({skill for posting in postings for skill in posting["skills"]})
selected = st.multiselect("Lọc kỹ năng (khớp ít nhất một)", languages)
filtered = [
    posting for posting in postings if not selected or set(selected).intersection(posting["skills"])
]
st.metric("Số tin trong bảng", len(filtered))
st.caption(
    "Đây là các dòng nguồn trong bộ lọc, chưa khử trùng tin giữa các dòng/nguồn. "
    "Một ngôn ngữ lặp trong tin chỉ xuất hiện một lần trong danh sách kỹ năng. "
    "SQL được xếp vào ngôn ngữ truy vấn; quy tắc bảo thủ có thể bỏ sót tên mơ hồ."
)
columns = [
    "source_id",
    "job_id",
    "job_url",
    "title",
    "description",
    "requirements",
    "skills",
    "skill_evidence",
    "skills_reason",
]
rows = [
    {
        **posting,
        "skills": json.dumps(posting["skills"], ensure_ascii=False),
        "skill_evidence": json.dumps(posting["skill_evidence"], ensure_ascii=False),
    }
    for posting in filtered
]
st.dataframe(rows, column_order=columns, hide_index=True)
st.subheader("Bằng chứng theo trường gốc")
evidence = [
    {"source_id": posting["source_id"], "job_url": posting["job_url"], **item}
    for posting in filtered
    for item in posting["skill_evidence"]
]
st.dataframe(evidence, hide_index=True)

output = io.StringIO()
writer = csv.DictWriter(output, fieldnames=columns)
writer.writeheader()
writer.writerows(rows)
csv_text = output.getvalue()
st.download_button(
    "Tải CSV theo bộ lọc (kèm bằng chứng)",
    csv_text.encode("utf-8-sig"),
    file_name=f"{source_id}-languages.csv",
    mime="text/csv",
)
with st.expander("Xem nội dung CSV sẽ tải"):
    st.code(csv_text, language="csv")
