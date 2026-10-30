"""Ephemeral profile upload and mapping; no prediction or training."""

import json

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Preview hồ sơ CSV", layout="wide")
st.title("Chuẩn hóa hồ sơ từ CSV")
st.write(
    "CSV UTF-8, tối đa 5 MiB và 10.000 dòng. Giữ thứ tự, chuỗi gốc và lỗi từng dòng; không cắt dữ liệu im lặng. Kinh nghiệm chỉ có số được hiểu là số năm."
)
st.info(
    "ML bị chặn: trang này chỉ chuẩn hóa và preview. Upload không sửa snapshot/model và không huấn luyện."
)
st.download_button(
    "Tải mẫu tên cột CSV", b"role,experience,skills,location\n", "profile-columns.csv", "text/csv"
)
uploaded = st.file_uploader("Chọn CSV hồ sơ", type=["csv"], max_upload_size=5)
separator = st.selectbox(
    "Dấu phân cách", [",", ";", "\t"], format_func=lambda v: "Tab" if v == "\t" else v
)
if uploaded is None:
    st.stop()
content = uploaded.getvalue()
service = MarketService()
try:
    inspected = service.profile_columns(content, separator)
except MarketError as error:
    st.error(str(error))
    st.stop()
mapping = {}
for field, label in [
    ("role", "Vai trò (bắt buộc)"),
    ("experience", "Kinh nghiệm (bắt buộc)"),
    ("skills", "Kỹ năng"),
    ("location", "Địa điểm"),
]:
    options = [None, *inspected["columns"]]
    mapping[field] = st.selectbox(
        f"Cột {label}",
        options,
        index=options.index(field) if field in options else 0,
        format_func=lambda v: v or "Chưa chọn",
        key=f"profile_{field}",
    )
if not mapping["role"] or not mapping["experience"]:
    st.info("Ghép hai cột bắt buộc để xem kết quả; các cột khác có thể để trống.")
    st.stop()
try:
    result = service.preview_profiles(content, mapping, separator)
except MarketError as error:
    st.error(str(error))
    st.stop()
a, b, c = st.columns(3)
a.metric("Tổng hồ sơ", result["row_count"])
b.metric("Chuẩn hóa hợp lệ", result["valid_count"])
c.metric("Hồ sơ có lỗi", result["error_count"])
visible = [
    {
        key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
        for key, value in row.items()
    }
    for row in result["rows"]
]
st.dataframe(visible, hide_index=True)
st.caption(
    "row_id theo thứ tự hồ sơ; csv_line là dòng bắt đầu bản ghi. Cảnh báo kỹ năng/địa điểm giữ nguyên để rà soát, không tự suy thành dữ liệu chắc chắn."
)
if not result["rows"]:
    st.info("CSV hiện chỉ có tên cột, chưa có hồ sơ dữ liệu.")
st.download_button(
    "Tải toàn bộ preview và lỗi CSV", result["csv"], "profile-preview.csv", "text/csv"
)
