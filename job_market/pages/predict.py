"""Salary-first demo using supported role/city inputs."""

import streamlit as st

from career_market import MarketError, MarketService

ROLES = {
    "Data/ML": "Dữ liệu & AI",
    "Backend": "Lập trình Backend",
    "Frontend": "Lập trình Frontend",
    "Fullstack": "Lập trình Fullstack",
    "Mobile": "Ứng dụng di động",
    "DevOps": "DevOps",
    "QA Automation": "Kiểm thử tự động",
}
CITIES = {"HN": "Hà Nội", "HCM": "TP. Hồ Chí Minh", "Đà Nẵng": "Đà Nẵng"}
last_inputs = st.session_state.get("salary_last_inputs", {"role": "Data/ML", "city": "HN"})

st.caption("LƯƠNG CNTT VIỆT NAM")
st.title("Dự đoán lương")
st.write("Chọn nghề và thành phố để xem mức lương chào tuyển ước tính.")
left, right = st.columns([1, 1.15], gap="large")
with left:
    with st.container(border=True):
        st.subheader("Thông tin công việc")
        with st.form("salary_demo"):
            role = st.selectbox(
                "Nghề nghiệp",
                list(ROLES),
                index=list(ROLES).index(last_inputs["role"]),
                format_func=ROLES.get,
                key="salary_role",
            )
            city = st.selectbox(
                "Thành phố",
                list(CITIES),
                index=list(CITIES).index(last_inputs["city"]),
                format_func=CITIES.get,
                key="salary_city",
            )
            submitted = st.form_submit_button(
                "Dự đoán lương", type="primary", use_container_width=True
            )
        st.caption("Có thể thử: Dữ liệu & AI tại Hà Nội hoặc TP. Hồ Chí Minh.")
    if submitted:
        st.session_state["salary_last_inputs"] = {"role": role, "city": city}
        try:
            st.session_state["salary_estimate"] = MarketService().estimate_salary(role, city)
        except MarketError as error:
            st.session_state["salary_estimate"] = {"status": "error", "message": str(error)}
with right:
    with st.container(border=True):
        result = st.session_state.get("salary_estimate")
        st.subheader("Mức lương ước tính")
        if result is None:
            st.metric("Triệu đồng / tháng", "—")
            st.caption("Kết quả xuất hiện sau khi bạn bấm dự đoán.")
        elif result["status"] == "ok":
            st.caption(f"{ROLES[result['role']]} · {CITIES[result['location']]}")
            st.metric("Triệu đồng / tháng", f"{result['salary_vnd_month'] / 1e6:.1f}")
            st.caption("Lương chào tuyển, chưa xác nhận gross hay net.")
            st.caption(
                f"Bản thử nghiệm · {result['dataset_count']} tin · Sai số kiểm tra khoảng {result['test_mae_vnd_month'] / 1e6:.0f} triệu/tháng."
            )
            with st.expander("Kết quả được tính thế nào?"):
                st.write(
                    f"Mô hình {result['model']} đã lưu. Có {result['support_count']} tin trong tập học khớp nghề và thành phố này."
                )
                st.write(
                    "Hiện ước tính theo nghề và thành phố; chưa tính tác động của kinh nghiệm hoặc kỹ năng riêng."
                )
        else:
            st.info(result["message"])
            st.caption("Chưa hiển thị lương khi lựa chọn thiếu dữ liệu.")
st.divider()
a, b = st.columns(2)
with a:
    st.page_link("pages/models.py", label="So sánh mô hình →")
with b:
    st.page_link("pages/market.py", label="Khám phá thị trường →")
