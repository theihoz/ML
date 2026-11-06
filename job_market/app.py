"""Điểm vào ứng dụng Streamlit: cấu hình trang và menu 5 trang."""

import streamlit as st

from career_market.ui.theme import apply_theme

st.set_page_config(page_title="Dự đoán lương CNTT", layout="wide")
apply_theme()

# Mục này: khai báo 5 trang; trang đầu tiên là trang chủ.
pages = [
    st.Page("pages/advisor.py", title="Tư vấn & dự đoán lương", default=True),
    st.Page("pages/overview.py", title="Tổng quan", url_path="Tong_quan"),
    st.Page("pages/market.py", title="Thị trường việc làm", url_path="Thi_truong"),
    st.Page("pages/evaluation.py", title="Đánh giá mô hình", url_path="Danh_gia"),
    st.Page("pages/dataset.py", title="Dữ liệu huấn luyện", url_path="Du_lieu_huan_luyen"),
]
navigation = st.navigation(pages, position="hidden")

# Mục này: thanh bên tự vẽ để kiểm soát tiêu đề và thứ tự liên kết.
with st.sidebar:
    st.markdown("### Lương CNTT")
    st.caption("Phân tích & dự đoán")
    for page in pages:
        st.page_link(page)
    st.divider()
    st.caption("Demo dữ liệu tuyển dụng Việt Nam")
navigation.run()
