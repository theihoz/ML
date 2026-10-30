"""Single-profile form; MarketService owns normalization and prediction status."""

import streamlit as st

from career_market import MarketService

st.set_page_config(page_title="Dự đoán lương chào tuyển", layout="wide")
st.title("Dự đoán lương chào tuyển")
st.info(
    "Suy luận/tư vấn chỉ mở khi artifact và dữ liệu đủ hỗ trợ hồ sơ. Run thăm dò đã lưu được trình bày ở trang Kết quả huấn luyện; hiện chưa có số năm kinh nghiệm được xác minh để hỗ trợ dự đoán theo kinh nghiệm."
)
st.caption(
    "Nhập nhóm nghề, kinh nghiệm (ví dụ 0, 2–4 năm, trên 3 năm), kỹ năng và địa điểm. "
    "Để trống thông tin chưa rõ; nhiều địa điểm ngăn bằng |. Remote là hình thức làm việc riêng."
)
with st.form("prediction_profile"):
    profile = {
        "role": st.text_input("Vai trò", key="prediction_role", placeholder="Backend"),
        "experience": st.text_input("Kinh nghiệm", key="prediction_experience"),
        "skills": st.text_input("Kỹ năng", key="prediction_skills"),
        "location": st.text_input("Địa điểm", key="prediction_location"),
        "work_mode": st.selectbox(
            "Hình thức làm việc",
            ["", "Remote"],
            key="prediction_work_mode",
            format_func=lambda value: value or "Chưa rõ",
        ),
    }
    submitted = st.form_submit_button("Kiểm tra hồ sơ")
if submitted:
    result = MarketService().predict_profile(profile)
    message = f"{result['status']}: {result['reason']}"
    if result["status"] == "invalid_input":
        st.error(message)
    else:
        st.warning(message)
    st.json(result)
