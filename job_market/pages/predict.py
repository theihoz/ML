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
MODELS = ["Ridge", "LinearRegression"]

st.caption("LƯƠNG CNTT VIỆT NAM")
st.title("Dự đoán lương")
st.write("Chọn nghề và thành phố để xem mức lương chào tuyển ước tính.")
left, right = st.columns([1, 1.15], gap="large")
with left:
    with st.container(border=True):
        st.subheader("Thông tin công việc")
        with st.form("salary_demo"):
            model_name = st.selectbox(
                "Mô hình",
                MODELS,
                index=MODELS.index(last_inputs.get("model", "Ridge")),
                format_func=lambda name: (
                    "Linear Regression" if name == "LinearRegression" else name
                ),
                key="salary_model",
            )
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
    if submitted:
        st.session_state["salary_last_inputs"] = {"role": role, "city": city, "model": model_name}
        try:
            st.session_state["salary_estimate"] = MarketService().estimate_salary(
                role, city, model_name=model_name
            )
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
            st.caption(
                f"{ROLES[result['role']]} · {CITIES[result['location']]} · {result['model']}"
            )
            st.metric("Triệu đồng / tháng", f"{result['salary_vnd_month'] / 1e6:.1f}")
        else:
            st.info(result["message"])
if result is not None and result["status"] == "ok":
    st.subheader("Lương ước tính theo thành phố")
    try:
        chart = MarketService().salary_scenarios(
            result["role"], result["location"], model_name=result["model"]
        )
        if chart["png"]:
            st.image(chart["png"], width="stretch")
    except MarketError:
        st.info("Chưa tải được biểu đồ. Kết quả dự đoán vẫn được giữ ở trên.")

st.divider()
a, b = st.columns(2)
with a:
    st.page_link("pages/models.py", label="So sánh mô hình →")
with b:
    st.page_link("pages/market.py", label="Khám phá thị trường →")
