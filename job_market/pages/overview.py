"""Trang Tổng quan — dashboard thị trường trên bộ salary-v2.

Mục này làm gì: 4 thẻ KPI + biểu đồ kỹ năng, kinh nghiệm, khu vực, vai trò.
"""

import streamlit as st

from career_market.ui import cache, charts

header, action = st.columns([4, 1], vertical_alignment="center")
with header:
    st.title("Tổng quan thị trường việc làm")
with action:
    if st.button("Tư vấn lương →", type="primary", width="stretch"):
        st.switch_page("pages/advisor.py")
with st.spinner("Đang tổng hợp dữ liệu…"):
    frame = cache.dataset()
    report = cache.report()
facts = charts.summary(frame)
selected = report["models"][report["selected"]]
st.caption(
    f"{facts['postings']:,} tin có công bố lương từ {facts['companies']} công ty · "
    "TopCV, VietnamWorks, ITviec, CareerViet, CareerBuilder"
)
# Mục này: 4 thẻ KPI (trung vị lương, top công nghệ, số vai trò, sai số mô hình).
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

# Mục này: các biểu đồ mô tả dữ liệu (không dùng mô hình).
left, right = st.columns(2, gap="medium")
with left, st.container(border=True, key="overview_chart_tech"):
    st.subheader("Ngôn ngữ & công nghệ có nhu cầu")
    st.caption("Toàn bộ kỹ năng, xếp theo số tin nhắc đến")
    st.image(cache.chart("skill_demand"), width="stretch")
with right, st.container(border=True, key="overview_chart_skill_salary"):
    st.subheader("Lương theo công nghệ")
    st.caption(
        "Toàn bộ kỹ năng, trung vị lương của tin nhắc đến · thanh xám: dưới 30 tin (ít dữ liệu)"
        " · đường đứt: trung vị chung"
    )
    st.image(cache.chart("skill_salary"), width="stretch")
left, right = st.columns(2, gap="medium")
with left, st.container(border=True, key="overview_chart_experience"):
    st.subheader("Kinh nghiệm & thu nhập")
    st.caption("Phân bố lương theo số năm kinh nghiệm yêu cầu · đường: trung vị")
    st.image(cache.chart("experience"), width="stretch")
with right, st.container(border=True, key="overview_chart_regions"):
    st.subheader("Lương theo khu vực")
    st.caption("Trung vị lương và số tin theo khu vực")
    st.image(cache.chart("regions"), width="stretch")
with st.container(border=True, key="overview_chart_roles"):
    st.subheader(f"So sánh lương theo vai trò · {facts['roles']} vai trò")
    st.caption("Hộp: 50% tin ở giữa · chấm: trung vị · n: số tin của vai trò")
    st.image(cache.chart("roles"), width="stretch")
with st.container(border=True, key="overview_chart_heatmap"):
    st.subheader("Lương theo vai trò và khu vực")
    st.caption("Trung vị lương (triệu VND/tháng); ô trống khi có dưới 3 tin")
    st.image(cache.chart("heatmap"), width="stretch")
st.page_link("pages/market.py", label="Xem phân tích chi tiết →")
