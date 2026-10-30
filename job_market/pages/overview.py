"""Overview dashboard inspired by the supplied reference, using real project data."""

import streamlit as st

from career_market import MarketError
from career_market.analytics_dashboard import overview_report

header, action = st.columns([4, 1], vertical_alignment="center")
with header:
    st.title("Tổng quan thị trường việc làm")
with action:
    if st.button("Dự đoán lương →", type="primary", width="stretch"):
        st.switch_page("pages/predict.py")
try:
    with st.spinner("Đang tổng hợp dữ liệu…"):
        report = overview_report()
except (MarketError, OSError) as error:
    st.error(str(error))
    st.stop()
st.caption(f"Tổng hợp từ {report['source_count']} bộ dữ liệu tuyển dụng Việt Nam")
cards = st.columns(4)
with cards[0], st.container(border=True, height=175, key="overview_kpi_salary"):
    value = report["mean_salary_vnd_month"]
    st.metric(
        "Lương trong tin",
        f"{value / 1e6:.1f} triệu" if value is not None else "—",
        help="Trung bình các trung điểm khoảng lương chào tuyển đã xác minh, đơn vị VND/tháng.",
    )
    st.caption(f"{report['salary_posting_count']} tin · mỗi tháng")
with cards[1], st.container(border=True, height=175, key="overview_kpi_tech"):
    st.caption("Công nghệ được nhắc nhiều")
    st.markdown("### " + " · ".join(report["top_skills"]))
    st.caption("Theo số tin tuyển dụng")
with cards[2], st.container(border=True, height=175, key="overview_kpi_models"):
    st.metric("Mô hình đã huấn luyện", str(report["model_count"]))
    st.caption("Ridge · Linear Regression")
with cards[3], st.container(border=True, height=175, key="overview_kpi_postings"):
    st.metric("Tin dùng phân tích", f"{report['posting_count']:,}")
    st.caption("Sau làm sạch và lọc nghề")

left, right = st.columns(2, gap="medium")
with left, st.container(border=True, key="overview_chart_tech"):
    st.subheader("Top 10 ngôn ngữ & công nghệ")
    st.caption("Xếp theo số tin nhắc đến")
    st.image(report["charts"]["skills"], width="stretch")
with right, st.container(border=True, key="overview_chart_experience"):
    st.subheader("Kinh nghiệm & thu nhập")
    st.caption(
        f"{report['experience_posting_count']} tin thu nhập tháng · khoảng kinh nghiệm yêu cầu"
    )
    if report["charts"]["experience"]:
        st.image(report["charts"]["experience"], width="stretch")
    else:
        st.info("Chưa có cặp kinh nghiệm và thu nhập được xác minh.")
left, right = st.columns(2, gap="medium")
with left, st.container(border=True, key="overview_chart_roles"):
    st.subheader("So sánh lương theo nghề")
    st.caption(f"{report['salary_posting_count']} tin · trung điểm lương VND/tháng")
    if report["charts"]["roles"]:
        st.image(report["charts"]["roles"], width="stretch")
    else:
        st.info("Chưa có dữ liệu lương.")
with right, st.container(border=True, key="overview_chart_regions"):
    st.subheader("Phân bố địa điểm")
    st.caption(f"Mỗi tin một nhóm địa điểm · Remote: {report['remote_count']} tin")
    st.image(report["charts"]["regions"], width="stretch")
    st.page_link("pages/market.py", label="Xem phân tích chi tiết →")
