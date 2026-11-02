"""Salary demo navigation with advanced audit routes hidden from the menu."""

import streamlit as st

from career_market.presentation import apply_theme

st.set_page_config(page_title="Dự đoán lương CNTT", layout="wide")
apply_theme()
pages = [
    st.Page("pages/advisor.py", title="Tư vấn & dự đoán lương", default=True),
    st.Page("pages/overview.py", title="Tổng quan", url_path="Tong_quan"),
    st.Page("pages/market.py", title="Thị trường việc làm", url_path="Thi_truong"),
    st.Page("pages/evaluation.py", title="Đánh giá mô hình", url_path="Danh_gia"),
    st.Page("pages/dataset.py", title="Dữ liệu huấn luyện", url_path="Du_lieu_huan_luyen"),
]
# Bản thăm dò 14 nhãn đã duyệt tay được giữ làm hồ sơ, không hiện trong menu chính.
for filename, title, url in [
    ("predict.py", "Dự đoán lương (thăm dò)", "Du_doan_tham_do"),
    ("models.py", "So sánh mô hình (thăm dò)", "Huan_luyen"),
    ("data.py", "Dữ liệu (thăm dò)", "Du_lieu"),
]:
    pages.append(st.Page(f"pages/{filename}", title=title, url_path=url))
for filename, title, url in [
    ("tools/sources.py", "Nguồn dữ liệu", "Nguon_du_lieu"),
    ("tools/download.py", "Tải lại nguồn", "Tai_nguon"),
    ("tools/roles.py", "Vai trò", "Vai_tro"),
    ("tools/locations.py", "Địa điểm", "Dia_diem"),
    ("tools/skills.py", "Kỹ năng", "Ky_nang"),
    ("tools/salary.py", "Lương", "Luong"),
    ("tools/experience.py", "Kinh nghiệm", "Kinh_nghiem"),
    ("tools/quality.py", "Chất lượng dữ liệu", "Chat_luong"),
    ("tools/time_coverage.py", "Độ phủ thời gian", "Do_phu_thoi_gian"),
    ("tools/preview_csv.py", "Preview hồ sơ CSV", "Preview_CSV"),
    ("tools/companies.py", "Đối chiếu công ty", "Cong_ty"),
    ("tools/preview_xlsx.py", "Preview hồ sơ Excel", "Preview_XLSX"),
    ("tools/split.py", "Train / validation / test", "Chia_tap"),
]:
    pages.append(st.Page(f"pages/{filename}", title=title, url_path=url))
navigation = st.navigation(pages, position="hidden")
with st.sidebar:
    st.markdown("### Lương CNTT")
    st.caption("Phân tích & dự đoán")
    for page in pages[:5]:
        st.page_link(page)
    st.divider()
    st.caption("Demo dữ liệu tuyển dụng Việt Nam")
navigation.run()
