"""Dashboard tổng quan trên bộ dữ liệu salary-v2: đủ mọi vai trò CNTT."""

import streamlit as st

from career_market import salary_app
from career_market import salary_charts as charts

header, action = st.columns([4, 1], vertical_alignment="center")
with header:
    st.title("Tổng quan thị trường việc làm")
with action:
    if st.button("Tư vấn lương →", type="primary", width="stretch"):
        st.switch_page("pages/advisor.py")
with st.spinner("Đang tổng hợp dữ liệu…"):
    frame = salary_app.dataset()
    report = salary_app.report()
facts = charts.summary(frame)
selected = report["models"][report["selected"]]
st.caption(
    f"{facts['postings']:,} tin có công bố lương từ {facts['companies']} công ty · "
    "TopCV, VietnamWorks, ITviec, CareerViet, CareerBuilder"
)
cards = st.columns(4)
with cards[0], st.container(border=True, height=175, key="overview_kpi_salary"):
    st.metric(
        "Trung vị lương",
        f"{facts['median']:.1f} triệu",
        help="Trung vị các trung điểm khoảng lương chào tuyển, VND/tháng.",
    )
    st.caption(f"Trung bình {facts['mean']:.1f} triệu · P90 {facts['p90']:.0f} triệu")
with cards[1], st.container(border=True, height=175, key="overview_kpi_tech"):
    st.caption("Công nghệ được nhắc nhiều")
    top = charts.skill_table(frame).nlargest(3, "postings")["skill"]
    st.markdown("### " + " · ".join(top))
    st.caption("Theo số tin tuyển dụng")
with cards[2], st.container(border=True, height=175, key="overview_kpi_models"):
    st.metric("Vai trò CNTT", str(facts["roles"]))
    st.caption(f"Mô hình tốt nhất: {selected['label']}")
with cards[3], st.container(border=True, height=175, key="overview_kpi_postings"):
    st.metric("Sai số MAE (test)", f"{selected['test']['MAE']:.2f} triệu")
    st.caption(f"R² = {selected['test']['R2']:.2f} trên {selected['test']['n']} tin test")

left, right = st.columns(2, gap="medium")
with left, st.container(border=True, key="overview_chart_tech"):
    st.subheader("Top 15 ngôn ngữ & công nghệ có nhu cầu")
    st.caption("Xếp theo số tin nhắc đến")
    st.image(salary_app.chart("skill_demand"), width="stretch")
with right, st.container(border=True, key="overview_chart_skill_salary"):
    st.subheader("Top 15 công nghệ lương cao nhất")
    st.caption("Trung vị lương của tin nhắc đến kỹ năng (≥ 30 tin) · đường đứt: trung vị chung")
    st.image(salary_app.chart("skill_salary"), width="stretch")
left, right = st.columns(2, gap="medium")
with left, st.container(border=True, key="overview_chart_experience"):
    st.subheader("Kinh nghiệm & thu nhập")
    st.caption("Phân bố lương theo số năm kinh nghiệm yêu cầu · đường: trung vị")
    st.image(salary_app.chart("experience"), width="stretch")
with right, st.container(border=True, key="overview_chart_regions"):
    st.subheader("Lương theo khu vực")
    st.caption("Trung vị lương và số tin theo khu vực")
    st.image(salary_app.chart("regions"), width="stretch")
with st.container(border=True, key="overview_chart_roles"):
    st.subheader(f"So sánh lương theo vai trò · {facts['roles']} vai trò")
    st.caption("Hộp: 50% tin ở giữa · chấm: trung vị · n: số tin của vai trò")
    st.image(salary_app.chart("roles"), width="stretch")
with st.container(border=True, key="overview_chart_heatmap"):
    st.subheader("Lương theo vai trò và khu vực")
    st.caption("Trung vị lương (triệu VND/tháng); ô trống khi có dưới 3 tin")
    st.image(salary_app.chart("heatmap"), width="stretch")
st.page_link("pages/market.py", label="Xem phân tích chi tiết →")
