"""Independent source download page; business rules live in MarketService."""

import os
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Tải nguồn đã duyệt", layout="wide")
st.title("Tải nguồn đã duyệt")
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
cache_dir = os.environ.get("CAREER_MARKET_CACHE_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
cache_path = Path(cache_dir) if cache_dir else None
sources = {source.source_id: source for source in service.sources()}
source_id = st.selectbox("Nguồn dữ liệu", list(sources))
source = sources[source_id]
st.caption(f"Catalog: {source.platform} · Kaggle v{source.revision} · {source.license}")
st.write(source.attribution)
st.link_button("Chứng cứ giấy phép / metadata Kaggle", source.metadata_url)
st.write(
    "Giấy phép do bên phát hành dataset khai báo. Khi bàn giao giữ attribution, metadata gốc "
    "và ghi rõ thay đổi nếu có chuẩn hóa."
)

result = None
if st.button("Tải hoặc dùng cache đã khớp"):
    try:
        with st.spinner("Kiểm tra revision, ZIP và raw…"):
            result = service.download_source(source_id, cache_dir=cache_path)
    except MarketError as error:
        st.error(str(error))
else:
    try:
        result = service.download_source(source_id, cache_dir=cache_path, check_only=True)
    except MarketError as error:
        st.warning(f"Chưa xác minh cache: {error}")

if result:
    action = "Đã tải" if result["status"] == "downloaded" else "Cache khớp"
    st.success(f"{action}: {source_id} v{source.revision} · SHA-256 ZIP và raw khớp catalog.")

missing = "Nguồn không cung cấp"
st.dataframe(
    [
        {"Loại thời gian": label, "Giá trị / ý nghĩa": value}
        for label, value in (
            (
                "Ngày đăng / thông báo",
                "; ".join(
                    f"{key}: {value}"
                    for key, value in source.time_fields.items()
                    if key in {"announcement_date", "date_posted"}
                )
                or missing,
            ),
            (
                "Hạn nộp",
                "expiration_date: " + source.time_fields["expiration_date"]
                if "expiration_date" in source.time_fields
                else missing,
            ),
            ("Ngày cập nhật tin", missing),
            ("Ngày nhập catalog", source.imported_on),
            ("Ngày tải (UTC)", result["downloaded_at"] if result else "Chưa xác minh"),
        )
    ],
    hide_index=True,
)
st.info(
    "Ngày tải và ngày nhập catalog không phải ngày đăng tin. Hạn nộp không phải ngày cập nhật. "
    "Tên dataset không xác định năm đăng của mọi tin."
)
if result:
    with st.expander("Manifest và checksum đã kiểm tra"):
        st.json(result)
