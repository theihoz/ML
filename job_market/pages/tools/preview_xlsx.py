"""XLSX upload, explicit sheet selection and shared profile normalization."""

import json

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Preview hồ sơ XLSX", layout="wide")
st.title("Chuẩn hóa hồ sơ từ XLSX")
st.write(
    "Chỉ XLSX: tối đa 5 MiB file, 20 MiB nội dung giải nén, 128 mục ZIP, "
    "20 sheet, 100 cột và 10.000 dòng hồ sơ mỗi sheet (ngoài dòng tên cột). "
    "CSV trung gian dùng chung chuẩn hóa cũng có giới hạn 5 MiB. "
    "Chọn sheet tường minh; không tự cắt dòng. Tên cột ở dòng 1, không trống/trùng. "
    "Chỉ nhận ô chuỗi/số/trống; từ chối macro, formula, liên kết ngoài, ngày, boolean và lỗi Excel. "
    "Kinh nghiệm dạng số được hiểu là số năm."
)
st.info(
    "Preview không cần model: chỉ chuẩn hóa và đối chiếu lỗi, không dự đoán hoặc huấn luyện. "
    "Upload không sửa dataset, snapshot hoặc model."
)
uploaded = st.file_uploader("Chọn XLSX hồ sơ", type=["xlsx"], max_upload_size=5)
if uploaded is None:
    st.stop()
content = uploaded.getvalue()
service = MarketService()
try:
    inspected = service.xlsx_sheets(content, filename=uploaded.name)
    sheet = st.selectbox(
        "Chọn sheet để preview",
        [None, *inspected["sheets"]],
        format_func=lambda value: value or "Chưa chọn sheet",
        key=inspected["input_sha256"],
    )
    if sheet is None:
        st.info("Chọn rõ một sheet trước khi ghép cột và preview.")
        st.stop()
    columns = service.xlsx_profile_columns(content, sheet, filename=uploaded.name)["columns"]
    st.write({"Sheet đã chọn": sheet, "Tên cột gốc": columns})
    mapping = {}
    for field, label in [
        ("role", "Vai trò (bắt buộc)"),
        ("experience", "Kinh nghiệm (bắt buộc)"),
        ("skills", "Kỹ năng"),
        ("location", "Địa điểm"),
    ]:
        options = [None, *columns]
        mapping[field] = st.selectbox(
            f"Cột {label}",
            options,
            index=options.index(field) if field in options else 0,
            format_func=lambda value: value or "Chưa chọn",
            key=f"xlsx_{inspected['input_sha256']}_{sheet}_{field}",
        )
    if not mapping["role"] or not mapping["experience"]:
        st.info("Ghép hai cột bắt buộc để xem kết quả; các cột khác có thể để trống.")
        st.stop()
    result = service.preview_xlsx_profiles(content, mapping, sheet, filename=uploaded.name)
except MarketError as error:
    st.error(str(error))
    st.stop()
st.write("Mapping đang dùng", result["mapping"])
a, b, c = st.columns(3)
a.metric("Tổng hồ sơ", result["row_count"])
b.metric("Chuẩn hóa hợp lệ", result["valid_count"])
c.metric("Hồ sơ có lỗi", result["error_count"])
st.dataframe(
    [
        {
            key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
            for key, value in row.items()
        }
        for row in result["rows"]
    ],
    hide_index=True,
)
st.caption(
    "row_id giữ thứ tự hồ sơ; source_row là số dòng trong sheet (tên cột ở dòng 1). "
    "Giữ raw và cả dòng trống/lỗi để đối chiếu. Hợp lệ chuẩn hóa chưa phải đủ điều kiện dự đoán."
)
if not result["rows"]:
    st.info("Sheet chỉ có tên cột, chưa có hồ sơ dữ liệu.")
st.download_button("Tải toàn bộ preview và lỗi CSV", result["csv"], "xlsx-preview.csv", "text/csv")
