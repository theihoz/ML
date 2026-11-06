"""Trang tư vấn nghề nghiệp: nhập hồ sơ, dự đoán lương và gợi ý kỹ năng nên học."""

import pandas as pd
import streamlit as st

from career_market import salary_app
from career_market import salary_charts as charts
from career_market.salary_dataset import REGIONS, ROLE_ORDER, SKILLS
from career_market.salary_model import MODEL_LABELS
from career_market.salary_visuals import png

report = salary_app.report()
models = [name for name in MODEL_LABELS if name != "Baseline"]
# Hồ sơ có thể truyền qua đường dẫn, ví dụ ?role=Data Engineer&years=3&skills=Python,SQL,
# để chia sẻ kết quả tư vấn; giá trị không hợp lệ bị bỏ qua.
query = st.query_params
shared = {
    "role": query.get("role") if query.get("role") in ROLE_ORDER else None,
    "region": query.get("region") if query.get("region") in REGIONS else None,
    "skills": [s for s in query.get("skills", "").split(",") if s in SKILLS],
}
try:
    shared["years"] = min(max(float(query.get("years", "")), 0.0), 20.0)
except ValueError:
    shared["years"] = None

st.caption("LƯƠNG CNTT VIỆT NAM")
st.title("Tư vấn & dự đoán lương")
st.write(
    "Nhập vai trò, kinh nghiệm và kỹ năng hiện có. Mô hình đã huấn luyện sẵn trên "
    f"{report['dataset_rows']:,} tin tuyển dụng sẽ ước tính mức lương và gợi ý kỹ năng nên học thêm."
)
left, right = st.columns([1, 1.25], gap="large")
with left, st.container(border=True):
    st.subheader("Hồ sơ của bạn")
    with st.form("advisor_form"):
        role = st.selectbox(
            "Vai trò", ROLE_ORDER, index=ROLE_ORDER.index(shared["role"] or "Backend Developer")
        )
        region = st.selectbox(
            "Khu vực làm việc", REGIONS, index=REGIONS.index(shared["region"] or REGIONS[0])
        )
        years = st.number_input(
            "Số năm kinh nghiệm",
            min_value=0.0,
            max_value=20.0,
            value=shared["years"] if shared["years"] is not None else 2.0,
            step=0.5,
        )
        skills = st.multiselect(
            "Kỹ năng đang có",
            list(SKILLS),
            default=shared["skills"] or ["Java", "SQL", "Git"],
            placeholder="Chọn ngôn ngữ, framework, công cụ…",
        )
        model_name = st.selectbox(
            "Mô hình",
            models,
            index=models.index(report["selected"]),
            format_func=lambda name: (
                MODEL_LABELS[name]
                + (" (tốt nhất trên valid)" if name == report["selected"] else "")
            ),
        )
        submitted = st.form_submit_button(
            "Dự đoán & tư vấn", type="primary", icon=":material/insights:", width="stretch"
        )
if shared["role"] and "advisor_result" not in st.session_state:
    submitted = True  # mở từ đường dẫn chia sẻ: tư vấn ngay với hồ sơ đã điền
if submitted:
    st.session_state["advisor_result"] = salary_app.advice(
        role, region, float(years), tuple(sorted(skills)), model_name
    )
    st.session_state["advisor_profile"] = {"role": role, "region": region, "years": years}
result = st.session_state.get("advisor_result")
with right, st.container(border=True):
    st.subheader("Mức lương ước tính")
    if result is None:
        st.metric("Triệu đồng / tháng", "—")
        st.caption("Kết quả xuất hiện sau khi bạn bấm Dự đoán & tư vấn.")
    else:
        profile = st.session_state["advisor_profile"]
        st.caption(
            f"{profile['role']} · {profile['region']} · {profile['years']:g} năm · "
            f"cấp bậc ước lượng {result['level']} · {result['model_label']}"
        )
        if result["supported"]:
            st.metric("Triệu đồng / tháng", f"{result['salary']:.1f}")
            st.write(
                f"Khoảng thường gặp (80% tin tương tự): "
                f"**{result['low']:.1f} – {result['high']:.1f}** triệu"
            )
        else:
            st.metric(
                "Khoảng lương (triệu đồng / tháng)", f"{result['low']:.0f} – {result['high']:.0f}"
            )
            st.warning(
                "Ít dữ liệu: chỉ hiện khoảng lương mở rộng, không hiện con số. "
                + " ".join(result["support_reasons"]),
                icon=":material/info:",
            )
        if not result["production_ready"]:
            st.caption("Mô hình chưa đạt chuẩn production; kết quả chỉ mang tính tham khảo.")
        market = result["market"]
        if market["role_median"] is not None:
            a, b = st.columns(2)
            a.metric("Trung vị thị trường của vai trò", f"{market['role_median']:.1f}")
            if result["supported"]:
                b.metric("Vị trí so với vai trò", f"P{market['percentile']:.0f}")
            st.caption(
                f"Dựa trên {market['role_postings']} tin của vai trò; 50% tin nằm trong "
                f"{market['role_p25']:.1f}–{market['role_p75']:.1f} triệu."
            )

if result is not None:
    st.subheader("Kỹ năng nên học thêm")
    recommendations = result["recommendations"]
    if recommendations:
        table = pd.DataFrame(recommendations)
        chart_col, table_col = st.columns([1.1, 1], gap="large")
        with chart_col:
            st.image(png(charts.recommendation_chart(recommendations)), width="stretch")
        with table_col:
            st.dataframe(
                table.rename(
                    columns={
                        "skill": "Kỹ năng",
                        "uplift": "Tăng lương (triệu)",
                        "demand_share": "Tỉ lệ tin yêu cầu",
                        "reason": "Lý do",
                    }
                ),
                hide_index=True,
                width="stretch",
                column_config={
                    "Tăng lương (triệu)": st.column_config.NumberColumn(format="%+.2f"),
                    "Tỉ lệ tin yêu cầu": st.column_config.ProgressColumn(
                        min_value=0, max_value=1, format="percent"
                    ),
                },
            )
        st.caption(
            "Tăng lương = lương dự đoán khi thêm đúng kỹ năng đó vào hồ sơ trừ lương hiện tại, "
            "giữ nguyên vai trò, kinh nghiệm và khu vực. Tỉ lệ tin yêu cầu tính trong cùng vai trò."
        )
    else:
        st.info("Hồ sơ đã có hầu hết kỹ năng phổ biến của vai trò này.")
    st.subheader("Lộ trình theo kinh nghiệm")
    path_col, _ = st.columns([2, 1])
    with path_col:
        st.image(png(charts.experience_path_chart(result["experience_path"])), width="stretch")
    st.caption(
        f"Sai số tuyệt đối trung bình của mô hình trên tập test: {result['test_mae']:.2f} triệu/tháng. "
        "Đây là lương chào tuyển ước tính, chưa phân biệt gross/net."
    )
