"""Trang chủ — Tư vấn & dự đoán lương.

Mục này làm gì: người dùng nhập hồ sơ → gọi model/advisor.py → hiện lương dự đoán,
kỹ năng nên học và lộ trình theo kinh nghiệm.
"""

import pandas as pd
import streamlit as st

from career_market.data.rules import COMPANY_TYPES, LEVELS, REGIONS, ROLE_ORDER, SKILLS
from career_market.model.estimators import MODEL_LABELS
from career_market.model.versions import freshness_line
from career_market.ui import cache, charts
from career_market.ui.charts import png

report = cache.report()
models = [name for name in MODEL_LABELS if name != "Baseline"]
# Hồ sơ có thể truyền qua đường dẫn, ví dụ ?role=Data Engineer&years=3&skills=Python,SQL,
# để chia sẻ kết quả tư vấn; giá trị không hợp lệ bị bỏ qua.
query = st.query_params
shared = {
    "skills_in_query": "skills" in query,
    "model": query.get("model") if query.get("model") in models else report["selected"],
    "role": query.get("role") if query.get("role") in ROLE_ORDER else None,
    "region": query.get("region") if query.get("region") in REGIONS else None,
    "skills": [s for s in query.get("skills", "").split(",") if s in SKILLS],
    "level": query.get("level") if query.get("level") in LEVELS else "Tự suy từ kinh nghiệm",
}
try:
    shared["years"] = min(max(float(query.get("years", "")), 0.0), 20.0)
except ValueError:
    shared["years"] = None
# Chỉ lấy mặc định URL khi mở phiên; cập nhật URL sau submit không đổi widget identity.
shared = st.session_state.setdefault("advisor_initial_profile", shared)

st.caption("LƯƠNG CNTT VIỆT NAM")
st.title("Tư vấn & dự đoán lương")
production = cache.validation().get("production") or {}
if not production.get("production_ready"):
    with st.container(horizontal=True, vertical_alignment="center"):
        st.info(
            "Kết quả mang tính tham khảo — mô hình chưa đạt chuẩn độ chính xác.",
            icon=":material/info:",
        )
        st.page_link(
            "pages/evaluation.py", label="Xem đánh giá mô hình", icon=":material/insights:"
        )
# Mục này: dòng độ mới của dữ liệu, đọc từ manifest phiên bản đang phục vụ (#111).
st.caption(freshness_line())
st.write(
    "Nhập vai trò, kinh nghiệm và kỹ năng hiện có. Mô hình đã huấn luyện sẵn trên "
    f"{report['dataset_rows']:,} tin tuyển dụng sẽ ước tính mức lương và gợi ý kỹ năng nên học thêm."
)
# Mục này: form nhập hồ sơ (cột trái) và kết quả lương (cột phải).
left, right = st.columns([1, 1.25], gap="large")
with left, st.container(border=True):
    st.subheader("Hồ sơ của bạn")
    with st.form("advisor_form"):
        role = st.selectbox(
            "Vai trò",
            ROLE_ORDER,
            key="advisor_role",
            index=ROLE_ORDER.index(shared["role"] or "Backend Developer"),
        )
        region = st.selectbox(
            "Khu vực làm việc",
            REGIONS,
            key="advisor_region",
            index=REGIONS.index(shared["region"] or REGIONS[0]),
        )
        level = st.selectbox(
            "Cấp bậc",
            ["Tự suy từ kinh nghiệm", *LEVELS],
            key="advisor_level",
            index=["Tự suy từ kinh nghiệm", *LEVELS].index(shared["level"]),
        )
        years = st.number_input(
            "Số năm kinh nghiệm",
            key="advisor_years",
            min_value=0.0,
            max_value=20.0,
            value=shared["years"] if shared["years"] is not None else 2.0,
            step=0.5,
        )
        skills = st.multiselect(
            "Kỹ năng đang có",
            list(SKILLS),
            key="advisor_skills",
            default=shared["skills"] if shared["skills_in_query"] else ["Java", "SQL", "Git"],
            placeholder="Chọn ngôn ngữ, framework, công cụ…",
        )
        with st.expander("Thêm thông tin (không bắt buộc)"):
            title = st.text_input(
                "Chức danh mong muốn", placeholder="Ví dụ: Senior Backend Engineer, Expert…"
            )
            company_type = st.selectbox(
                "Loại công ty", ["Khác", *[name for name, _ in COMPANY_TYPES]]
            )
            work_mode = st.selectbox("Hình thức làm việc", ["Không rõ", "Toàn thời gian", "Từ xa"])
        model_name = st.selectbox(
            "Mô hình",
            models,
            key="advisor_model",
            index=models.index(shared["model"]),
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
    st.session_state["advisor_result"] = cache.advice(
        role,
        region,
        float(years),
        tuple(sorted(skills)),
        model_name,
        None if level == "Tự suy từ kinh nghiệm" else level,
        title.strip(),
        company_type,
        work_mode,
    )
    st.session_state["advisor_profile"] = {"role": role, "region": region, "years": years}
    st.query_params.update(
        {
            "role": role,
            "region": region,
            "years": str(years),
            "skills": ",".join(sorted(skills)),
            "model": model_name,
            "level": level if level != "Tự suy từ kinh nghiệm" else "",
        }
    )
result = st.session_state.get("advisor_result")
with right, st.container(border=True):
    st.subheader("Lương thị trường gross · gần đúng")
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
            # Khoảng lương là thông tin chính (#82, #114); trung vị là mức điển hình.
            interval = result["salary_range"]
            st.metric(
                "Khoảng lương (triệu đồng / tháng)",
                f"{interval['p25']:.1f} – {interval['p75']:.1f}",
            )
            st.markdown(
                f"Mức điển hình khoảng **{interval['median']:.1f} triệu**; một nửa số tin tương tự "
                "nằm trong khoảng trên."
            )
            st.markdown(
                f"Dựa trên {result['cohort_rows']} tin cùng vai trò và cấp bậc trong dữ liệu."
            )
            st.caption(
                "Gross thị trường gần đúng sau hiệu chỉnh theo báo cáo. Độ rộng p25–p75 lấy từ độ "
                "phân tán lương chào tuyển valid; không phải phân vị khảo sát gross hay khoảng tin cậy."
            )
        else:
            # Ít dữ liệu (#89): chỉ hiện khoảng mở rộng, không hiện con số.
            st.metric(
                "Khoảng lương (triệu đồng / tháng)", f"{result['low']:.0f} – {result['high']:.0f}"
            )
            st.warning("Ít dữ liệu: " + result["support_message"], icon=":material/info:")
            with st.expander("Vì sao?"):
                st.markdown(
                    "Con số lương chỉ hiện khi nhóm vai trò × cấp bậc có ít nhất 20 tin có lương "
                    "và mô hình đạt độ chính xác cho vai trò, cấp bậc đó. Khoảng lương được mở "
                    "rộng để vẫn chứa lương thật trong phần lớn trường hợp."
                )
                for reason in result["support_reasons"]:
                    st.markdown(f"- {reason}")
        advertised = result["advertised_range"]
        if result["supported"]:
            st.caption(
                f"Lương chào tuyển ước tính (chưa rõ gross/net): "
                f"{advertised['p25']:.1f} – {advertised['median']:.1f} – "
                f"{advertised['p75']:.1f} triệu/tháng."
            )
        for warning in result["calibration"]["warnings"]:
            st.warning(warning)
        for warning in result["data_sufficiency"]["warnings"]:
            st.warning(warning)
        market = result["market"]
        if market["role_median"] is not None:
            st.caption(
                f"Trung vị lương chào tuyển trong {market['role_postings']} tin của vai trò: "
                f"{market['role_median']:.1f} triệu/tháng."
            )

# Mục này: gợi ý kỹ năng + lộ trình kinh nghiệm, chỉ hiện sau khi bấm nút.
if result is not None:
    st.subheader("Kỹ năng nên học thêm")
    recommendations = result["recommendations"]
    if recommendations and not result["supported"]:
        # Mức tăng tính từ một dự đoán chưa đủ tin cậy nên không hiện số tiền.
        table = pd.DataFrame(recommendations)[["skill", "demand_share", "reason"]]
        table["reason"] = table["reason"].replace({"Tăng lương dự đoán": "Có thể giúp tăng lương"})
        st.dataframe(
            table.rename(
                columns={"skill": "Kỹ năng", "demand_share": "Tỉ lệ tin yêu cầu", "reason": "Lý do"}
            ),
            hide_index=True,
            width="stretch",
            column_config={
                "Tỉ lệ tin yêu cầu": st.column_config.ProgressColumn(
                    min_value=0, max_value=1, format="percent"
                ),
            },
        )
        st.caption("Hồ sơ ít dữ liệu nên không hiện mức tăng lương ước tính cho từng kỹ năng.")
    elif recommendations:
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
        "MAE đo trên lương chào tuyển chưa rõ gross/net; lộ trình và mức tăng dùng gross thị trường gần đúng."
    )
