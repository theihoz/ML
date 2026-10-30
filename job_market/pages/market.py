"""Demand and salary views; observed values stay separate from model estimates."""

import pandas as pd
import streamlit as st

from career_market import MarketError
from career_market.analytics_dashboard import salary_report
from career_market.dashboard import render_dashboard

st.title("Thị trường việc làm")
view = st.radio(
    "Khám phá",
    ["Nhu cầu tuyển dụng", "Mức lương", "Kinh nghiệm"],
    horizontal=True,
    key="market_view",
)
if view == "Nhu cầu tuyển dụng":
    render_dashboard(show_title=False)
else:
    default = 1 if view == "Kinh nghiệm" else 0
    cohort = st.selectbox(
        "Dữ liệu",
        ["salary", "income"],
        index=default,
        format_func=lambda value: (
            "Lương chào tuyển · 2026" if value == "salary" else "Thu nhập tháng · 2023"
        ),
        help="Hai nhóm được phân tích riêng để không trộn lương và thu nhập.",
        key="salary_cohort_" + view,
    )
    try:
        requested = ("experience",) if view == "Kinh nghiệm" else ("roles", "regions", "skills")
        report = salary_report(cohort, requested)
    except MarketError as error:
        st.error(str(error))
        st.stop()
    st.caption(f"{report['posting_count']} tin · VND/tháng · gross/net chưa rõ")
    if view == "Mức lương":
        left, right = st.columns(2)
        for column, key in [(left, "roles"), (right, "regions")]:
            with column:
                if report["charts"][key]:
                    st.image(report["charts"][key], width="stretch")
                else:
                    st.info("Chưa có số liệu cho biểu đồ này.")
        st.subheader(f"Kỹ năng và {report['quantity']} trong tin")
        if report["charts"]["skills"]:
            st.image(report["charts"]["skills"], width="stretch")
        else:
            st.info("Nhóm này chưa có kỹ năng được ghi rõ.")
        with st.expander("Xem số liệu"):
            for key, title in [
                ("roles", "Theo nghề"),
                ("regions", "Theo khu vực"),
                ("skills", "Theo kỹ năng"),
            ]:
                st.write(title)
                table = pd.DataFrame(report[key]).rename(
                    columns={
                        "name": "Nhóm",
                        "posting_count": "Số tin",
                        "mean_vnd_month": f"Trung điểm {report['quantity']} TB (VND/tháng)",
                    }
                )
                st.dataframe(table, hide_index=True)
            st.caption(
                "Một tin nhiều địa điểm được tính một lần trong từng khu vực. Mức lương gắn với kỹ năng không chứng minh kỹ năng đó gây tăng lương."
            )
    elif report["charts"]["experience"]:
        st.subheader("Kinh nghiệm và thu nhập")
        st.image(report["charts"]["experience"], use_container_width=True)
        st.caption(
            "Đường ngang là khoảng kinh nghiệm yêu cầu trong tin. Hai tin chưa đủ để kết luận xu hướng."
        )
    else:
        st.info(
            "Nhóm này chưa có kinh nghiệm theo năm được xác minh. Chọn Thu nhập tháng · 2023 để xem các tin có thông tin này."
        )
