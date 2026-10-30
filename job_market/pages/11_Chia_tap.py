"""Display the structural allocation without authorizing training."""

import json

import streamlit as st

from career_market import MarketError, MarketService
from career_market.dashboard import prepared_report

st.title("Chia train / validation / test")
st.write("Mục tiêu 70% / 15% / 15%, seed 42. Giữ nguyên nhóm công ty và tin trùng/đăng lại.")
service = MarketService()
try:
    prepared = prepared_report(service)
    cohorts = service.company_report(prepared["rows"])["split_readiness"]["cohorts"]
except MarketError as error:
    st.error(str(error))
    st.stop()
if not cohorts:
    st.warning("Chưa có cohort có nhãn lương hợp lệ.")
    st.stop()
cohort = st.selectbox(
    "Nhóm nhãn",
    cohorts,
    format_func=lambda c: f"{c['salary_basis']} · {c['compensation_scope']}",
)
result = service.preview_split(
    prepared["rows"], basis=cohort["salary_basis"], scope=cohort["compensation_scope"]
)
st.warning("Chỉ xem trước cấu trúc. Cần duyệt đủ dữ liệu và khóa policy trước huấn luyện.")
st.write(f"{result['eligible_entities']} tin có nhãn · {result['eligible_groups']} nhóm độc lập")
if result["status"] == "blocked":
    st.error("Chưa tạo được ba tập không rỗng. Không cắt nhóm để ép tỷ lệ.")
st.json({key: value for key, value in result.items() if key != "membership"})
if result["membership"]:
    st.dataframe(result["membership"], hide_index=True)
st.download_button(
    "Tải báo cáo preview JSON",
    json.dumps(result, ensure_ascii=False, indent=2),
    "split-preview.json",
    "application/json",
)
