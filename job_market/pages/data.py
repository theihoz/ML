"""Readable data tables; technical audits are optional."""

import pandas as pd
import streamlit as st

from career_market import MarketError, MarketService
from career_market.dashboard import prepared_report

st.title("Dữ liệu")
kind = st.radio(
    "Xem dữ liệu", ["Dùng để dự đoán lương", "Dùng để phân tích thị trường"], horizontal=True
)
try:
    if kind == "Dùng để dự đoán lương":
        verified = MarketService().training_readiness()
        rows = verified["labels"]["rows"]
        membership = {r["entity_id"]: r["split"] for r in verified["split"]["membership"]}
        st.caption(
            f"{len(rows)} tin · {verified['labels']['company_count']} công ty · lương VND/tháng"
        )
    else:
        rows = prepared_report(MarketService())["eda"]
        st.caption(f"{len(rows)} tin sau làm sạch")
except (MarketError, OSError, ValueError) as error:
    st.error(str(error))
    st.stop()
role = st.selectbox("Lọc nghề", ["Tất cả", *sorted({row["role"] for row in rows})])
table = pd.DataFrame(
    [
        {
            "Công việc": row["title_raw"],
            "Nghề": row["role"],
            "Công ty": row.get("company_raw", ""),
            "Địa điểm": ", ".join(row["locations"]),
            "Lương trong tin": row.get("salary_raw", ""),
            "Trung điểm lương (triệu/tháng)": (
                row["salary_target_vnd_month"] / 1e6 if row.get("salary_target_vnd_month") else None
            ),
            "Mục đích": {"train": "Học", "validation": "Chọn mô hình", "test": "Kiểm tra"}.get(
                membership.get(row["posting_id"]) if kind == "Dùng để dự đoán lương" else None,
                "Phân tích thị trường",
            ),
        }
        for row in rows
        if role == "Tất cả" or row["role"] == role
    ]
)
st.dataframe(table, hide_index=True, use_container_width=True)
st.download_button("Tải bảng dữ liệu", table.to_csv(index=False), "du-lieu.csv", "text/csv")
with st.expander("Công cụ kiểm tra dữ liệu"):
    if kind == "Dùng để dự đoán lương":
        st.markdown(
            "[Vietnam IT Job Posts · phiên bản 1](https://www.kaggle.com/datasets/vitthnhnguyn138/vietnam-it-job-posts)"
        )
        st.caption("Việt Thành Nguyễn · Giấy phép MIT theo khai báo nguồn.")
    else:
        st.page_link("pages/tools/quality.py", label="Đối chiếu trước và sau làm sạch")
        st.page_link("pages/tools/sources.py", label="Nguồn phân tích và giấy phép")
    st.page_link("pages/tools/preview_csv.py", label="Kiểm tra file CSV")
    st.page_link("pages/tools/preview_xlsx.py", label="Kiểm tra file Excel")
