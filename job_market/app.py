"""Local EDA dashboard using the shared business service."""

import streamlit as st

from career_market.dashboard import render_dashboard

pages = [st.Page(render_dashboard, title="Phân tích nhu cầu", default=True)]
for filename, title, url in [
    ("0_Nguon_du_lieu.py", "Nguồn dữ liệu", "Nguon_du_lieu"),
    ("1_Tai_nguon.py", "Tải lại nguồn", "Tai_nguon"),
    ("2_Vai_tro.py", "Vai trò", "Vai_tro"),
    ("3_Dia_diem.py", "Địa điểm", "Dia_diem"),
    ("4_Ky_nang.py", "Kỹ năng", "Ky_nang"),
    ("5_Luong.py", "Lương", "Luong"),
    ("6_Kinh_nghiem.py", "Kinh nghiệm", "Kinh_nghiem"),
    ("7_Chat_luong.py", "Chất lượng dữ liệu", "Chat_luong"),
    ("8_Do_phu_thoi_gian.py", "Độ phủ thời gian", "Do_phu_thoi_gian"),
    ("9_Preview_CSV.py", "Preview hồ sơ CSV", "Preview_CSV"),
    ("10_Du_doan.py", "Dự đoán lương", "Du_doan"),
    ("10_Cong_ty.py", "Đối chiếu công ty", "Cong_ty"),
    ("10_Preview_XLSX.py", "Preview hồ sơ Excel", "Preview_XLSX"),
    ("11_Chia_tap.py", "Train / validation / test", "Chia_tap"),
]:
    pages.append(st.Page(f"pages/{filename}", title=title, url_path=url))
st.navigation(pages, expanded=True).run()
