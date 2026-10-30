"""Streamlit presentation of filtered, observed skill demand."""

import hashlib
import os
from pathlib import Path

import streamlit as st

from .preparation import RULES_VERSION
from .service import MarketError, MarketService


@st.cache_data(show_spinner=False)
def _prepare(raw_dir, signature):
    return MarketService(raw_dir=Path(raw_dir)).prepare()


def prepared_report(service):
    try:
        review_dir = service.raw_dir.parent / "labels/2026-10-29"
        review_signature = tuple(
            (path.name, hashlib.sha256(path.read_bytes()).hexdigest())
            for path in sorted(review_dir.glob("*"))
            if path.suffix in {".json", ".csv"}
        )
        signature = (RULES_VERSION, review_signature) + tuple(
            (
                s.source_id,
                (service.raw_dir / s.filename).stat().st_mtime_ns,
                (service.raw_dir / s.filename).stat().st_size,
            )
            for s in service.sources()
        )
    except OSError as error:
        raise MarketError(f"Không đọc được dữ liệu nguồn: {error}") from error
    return _prepare(str(service.raw_dir), signature)


def render_dashboard(show_title=True):
    st.set_page_config(page_title="Thị trường việc làm CNTT", layout="wide")
    if show_title:
        st.title("Thị trường việc làm")
    st.caption("Khám phá kỹ năng được nhắc trong tin tuyển dụng CNTT Việt Nam.")
    raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
    service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
    try:
        report = prepared_report(service)
    except MarketError as error:
        st.error(str(error))
        st.stop()
    sources = {source.source_id: source for source in service.sources()}
    chosen = st.multiselect(
        "Nguồn dữ liệu",
        list(sources),
        default=["jobs-2026"],
        format_func=lambda key: (
            "TopCV · 2025–2026" if key == "jobs-2026" else "CareerBuilder · 2023"
        ),
    )
    left, middle, right = st.columns(3)
    roles = sorted({r["role"] for r in report["eda"]})
    role = left.selectbox(
        "Nhóm nghề", [None, *roles], format_func=lambda v: v or "Tất cả", key="demand_role"
    )
    places = sorted({p for r in report["eda"] for p in r["locations"]})
    locations = middle.multiselect("Địa điểm (khớp ít nhất một)", places, key="demand_locations")
    mode = right.selectbox(
        "Hình thức", [None, "Remote"], format_func=lambda v: v or "Tất cả", key="demand_mode"
    )
    result = service.skill_demand(
        report["eda"], role=role, locations=locations, work_mode=mode, source_ids=chosen
    )
    a, b, c = st.columns(3)
    a.metric("Tin tuyển dụng", result["posting_count"])
    b.metric("Tin có kỹ năng", result["with_skill_count"])
    c.metric("Kỹ năng hiển thị", len(result["table"]))
    if "jobs-2026" in chosen:
        st.caption("TopCV: kỹ năng lấy từ tiêu đề · Tin đăng 12/2025–01/2026.")
    if len(chosen) > 1:
        st.caption("Các nguồn khác phạm vi thu thập; chưa dùng để kết luận xu hướng nhiều năm.")
    st.subheader("Top kỹ năng được nhắc trong tin")
    st.image(result["png"])
    st.dataframe(result["table"], hide_index=True)
    st.download_button("Tải bảng CSV theo bộ lọc", result["csv"], "skill-demand.csv", "text/csv")
    st.download_button(
        "Tải biểu đồ PNG theo bộ lọc", result["png"], "skill-demand.png", "image/png"
    )
    with st.expander("Quy mô và xuất xứ"):
        st.write("Một tin chỉ tính một lần; số liệu mô tả dataset, không đại diện toàn thị trường.")
        st.caption(result["scope"])
        st.json(report["summary"])
        st.json(report["reviewed_labels"])
        for key in chosen:
            st.write(sources[key].attribution)
