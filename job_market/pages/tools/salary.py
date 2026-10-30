"""Compare salary fields with strict normalization and export review evidence."""

import os
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Lương chào tuyển", layout="wide")
st.title("Lương chào tuyển")
st.write(
    "Giữ hai đầu khoảng lương; chỉ tính trung điểm khi có tiền tệ và kỳ trả lương rõ ràng. "
    "Không đổi ngoại tệ hoặc quy đổi gross/net."
)
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
selected = st.selectbox(
    "Nguồn dữ liệu", ["Tất cả"] + [source.source_id for source in service.sources()]
)
try:
    report = service.salary_report(None if selected == "Tất cả" else selected)
except MarketError as error:
    st.error(str(error))
    st.stop()

st.metric("Số dòng thô đã phân tích", report["row_count"])
st.metric("Nhãn đủ VND/tháng (n)", report["target_n"])
st.caption(
    "Đây là số dòng nguồn, chưa lọc vai trò hoặc khử trùng. "
    "Kỳ lương chỉ lấy từ trường salary, không suy từ JD hay tiêu đề. "
    "USD/năm giữ đơn vị riêng; thiếu đơn vị thì trung điểm và target để trống."
)
st.dataframe(report["rows"], hide_index=True)
st.subheader("Số dòng theo lý do")
st.dataframe(
    [{"salary_reason": reason, "n": count} for reason, count in report["reason_counts"].items()],
    hide_index=True,
)
st.write("Theo nguồn:", report["source_counts"])
st.write("Theo trạng thái:", report["status_counts"])
st.info("ML bị chặn trong đợt EDA. Trang này không huấn luyện hoặc dự đoán.")
st.caption("Review CSV giữ mọi dòng chưa có target, kể cả thỏa thuận và đơn vị ngoài VND/tháng.")
for filename, content in service.salary_exports(report).items():
    st.download_button(
        f"Tải {filename}", content.encode("utf-8-sig"), file_name=filename, mime="text/csv"
    )

st.subheader("Đối chiếu một chuỗi lương")
raw_salary = st.text_input("Chuỗi lương cần kiểm tra")
if raw_salary:
    st.json(service.normalize_salary(raw_salary))
