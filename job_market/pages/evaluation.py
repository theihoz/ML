"""Trang Đánh giá mô hình — đọc kết quả đã lưu, không huấn luyện lại.

Mục này làm gì: so sánh MAE/RMSE/R²/MAPE, thực tế–dự đoán, đặc trưng quan trọng,
rồi kiểm định độ tin cậy (hiệu chuẩn, bootstrap, công bằng).
"""

import pandas as pd
import streamlit as st

from career_market.model.estimators import MODEL_LABELS
from career_market.paths import artifacts_dir
from career_market.ui import cache, charts
from career_market.ui.charts import png

st.title("Đánh giá mô hình")
report = cache.report()
split = report["split"]
st.caption(
    f"Train {split['train']:,} · Valid {split['valid']:,} · Test {split['test']:,} tin "
    "· chia theo công ty · đơn vị triệu VND/tháng"
)
part = st.segmented_control(
    "Đánh giá trên",
    ["test", "valid", "train"],
    default="test",
    format_func={"test": "Tập test", "valid": "Tập valid", "train": "Tập train"}.get,
    key="evaluation_part",
)
part = part or "test"
selected = report["models"][report["selected"]][part]
st.subheader(f"Mô hình được chọn: {report['models'][report['selected']]['label']}")
a, b, c, d = st.columns(4)
a.metric("MAPE", f"{selected['MAPE']:.1f}%")
b.metric("MAE", f"{selected['MAE']:.2f}")
c.metric("RMSE", f"{selected['RMSE']:.2f}")
d.metric("R²", f"{selected['R2']:.3f}")
# Mục này: bảng so sánh 4 mô hình trên tập đang chọn.
rows = [
    {
        "Mô hình": values["label"],
        "Siêu tham số": ", ".join(f"{k}={v}" for k, v in values["params"].items()) or "—",
        "MAE": values[part]["MAE"],
        "RMSE": values[part]["RMSE"],
        "R²": values[part]["R2"],
        "MAPE (%)": values[part]["MAPE"],
        "Số tin": values[part]["n"],
    }
    for values in report["models"].values()
]
table = pd.DataFrame(rows)
st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    column_config={
        name: st.column_config.NumberColumn(format="%.3f")
        for name in ("MAE", "RMSE", "R²", "MAPE (%)")
    },
)
st.download_button("Tải bảng metric CSV", table.to_csv(index=False), "metrics.csv", "text/csv")
st.image(png(charts.model_comparison(report, part)), width="stretch")
st.caption(
    "Mô hình được chọn theo MAE nhỏ nhất trên tập valid; tập test chỉ dùng để báo cáo cuối cùng."
)
# Mục này: phân tích lỗi trên tập test.
predictions = pd.read_csv(artifacts_dir() / "test_predictions.csv")
left, right = st.columns(2, gap="medium")
with left, st.container(border=True):
    st.subheader("Thực tế và dự đoán (tập test)")
    st.image(png(charts.actual_vs_predicted(predictions)), width="stretch")
with right, st.container(border=True):
    st.subheader("Mức độ quan trọng của đặc trưng")
    st.image(cache.chart("importance"), width="stretch")
left, right = st.columns(2, gap="medium")
with left, st.container(border=True):
    st.subheader("Kỹ năng mang lại giá trị gia tăng thu nhập")
    st.caption("Mức tăng lương dự đoán trung bình khi bổ sung kỹ năng, các yếu tố khác giữ nguyên")
    st.image(cache.chart("uplift"), width="stretch")
with right, st.container(border=True):
    st.subheader("Sai số theo vai trò (tập test)")
    st.image(png(charts.error_by_role(predictions)), width="stretch")
with st.expander("Kết quả dò siêu tham số trên tập valid"):
    for name, trials in report["tuning"].items():
        st.write(f"**{report['models'][name]['label']}**")
        st.dataframe(pd.DataFrame(trials), hide_index=True, width="stretch")

# Mục này: kiểm định (model/validation.py) — mô hình có đáng tin không.
st.header("Kiểm định độ tin cậy của mô hình")
check = cache.validation()
production = check["production"]
STANDARD_LABELS = {
    "median_error_pct": "Trung vị sai số %",
    "within_20_pct": "Tỉ lệ sai ≤ 20%",
    "coverage_pct": "Độ phủ khoảng p10–p90 (%)",
}
STATUS_LABELS = {"pass": "Đạt", "fail": "Không đạt", "not_scored": "Không chấm (< 20 tin test)"}


def _limit(value):
    """Viết ngưỡng dạng chữ (một số, hoặc khoảng "a–b")."""
    return f"{value[0]}–{value[1]}" if isinstance(value, list | tuple) else str(value)


with st.container(border=True, key="production_standard"):
    st.subheader("Chuẩn production")
    if production["production_ready"]:
        st.success("Mô hình đang phục vụ đạt chuẩn production.")
    else:
        st.warning(
            "Mô hình đang phục vụ chưa đạt chuẩn production: kết quả chỉ mang tính tham khảo."
        )
    st.caption(
        "So cận bất lợi của khoảng tin cậy bootstrap 95% (lấy mẫu lại theo công ty) với ngưỡng; "
        "chỉ số theo cách Glassdoor và LinkedIn Salary công bố."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Chỉ số": STANDARD_LABELS[name],
                    "Giá trị": round(metric["point"], 1),
                    "Khoảng 95%": "{:.1f} – {:.1f}".format(*metric["ci95"]),
                    "Ngưỡng": _limit(metric["threshold"]),
                    "Kết quả": "Đạt" if metric["pass"] else "Không đạt",
                }
                for name, metric in production["overall"]["metrics"].items()
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    goal = production["thresholds"]["long_term"]
    st.caption(
        f"Mục tiêu dài hạn (mức Glassdoor): trung vị sai số ≤ {goal['median_error_pct']}% và "
        f"≥ {goal['within_20_pct']}% dự đoán sai không quá 20%."
    )
    for column, label in (("role", "Theo vai trò"), ("level", "Theo cấp bậc")):
        st.caption(label)
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Nhóm": row["group"],
                        "Số tin test": row["n"],
                        "Kết quả": STATUS_LABELS[row["status"]],
                        **{
                            STANDARD_LABELS[name]: round(metric["point"], 1)
                            for name, metric in row.get("metrics", {}).items()
                        },
                    }
                    for row in production[column]
                ]
            ),
            hide_index=True,
            width="stretch",
        )
boot = check["bootstrap"]
st.caption(
    f"Tính trên {check['test_rows']} tin test của {boot['companies']} công ty; "
    f"bootstrap {boot['rounds']} lần, lấy mẫu lại theo công ty."
)
calibration_tab, bootstrap_tab, fairness_tab = st.tabs(
    ["Hiệu chuẩn khoảng dự đoán", "Bootstrap", "Công bằng theo nhóm"]
)
with calibration_tab:
    levels = pd.DataFrame(check["calibration"]["levels"])
    cols = st.columns(len(levels))
    for col, row in zip(cols, levels.itertuples()):
        col.metric(
            f"Khoảng {row.level:.0%}",
            f"{row.coverage:.1%}",
            f"{(row.coverage - row.level) * 100:+.1f} điểm %",
            delta_color="off",
        )
    left, right = st.columns(2, gap="medium")
    with left:
        st.image(cache.chart("reliability"), width="stretch")
    with right:
        st.caption("Tỉ lệ bao phủ của khoảng 80% theo mức lương thật")
        st.dataframe(
            pd.DataFrame(check["calibration"]["by_salary_band"]), hide_index=True, width="stretch"
        )
        st.caption("Vai trò bao phủ kém nhất (khoảng 80%)")
        st.dataframe(
            pd.DataFrame(check["calibration"]["by_role"][:6]), hide_index=True, width="stretch"
        )
with bootstrap_tab:
    rows = [
        {
            "Mô hình": MODEL_LABELS[name],
            "MAE": values["MAE"]["point"],
            "MAE 95%": "{:.2f} – {:.2f}".format(*values["MAE"]["ci95"]),
            "R²": values["R2"]["point"],
            "R² 95%": "{:.3f} – {:.3f}".format(*values["R2"]["ci95"]),
        }
        for name, values in boot["models"].items()
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    differences = [
        {
            "So với": MODEL_LABELS[name],
            "Chênh MAE trung bình": values["mean"],
            "Khoảng 95%": "{:.2f} – {:.2f}".format(*values["ci95"]),
            "Tỉ lệ lần Gradient Boosting tốt hơn": f"{values['p_better']:.1%}",
        }
        for name, values in boot["differences"].items()
    ]
    st.dataframe(pd.DataFrame(differences), hide_index=True, width="stretch")
    st.image(cache.chart("bootstrap"), width="stretch")
with fairness_tab:
    groups = check["fairness"]
    column = (
        st.segmented_control(
            "Nhóm",
            list(groups),
            default="region",
            format_func=lambda key: groups[key]["label"],
            key="fairness_group",
        )
        or "region"
    )
    st.image(cache.chart("fairness", column), width="stretch")
    st.dataframe(pd.DataFrame(groups[column]["groups"]), hide_index=True, width="stretch")
    gender = check["gender"]
    st.caption(
        f"Giới tính: dữ liệu không có thông tin giới tính ứng viên và mô hình không dùng giới tính. "
        f"{gender['mentioned']} tin ({gender['share_pct']:.2f}%) ghi điều kiện giới tính trong nội dung "
        "— quá ít để đo thống kê; đây là dấu hiệu phân biệt cần cảnh báo khi đăng tin."
    )


st.header("Độ chính xác thực tế")
reality = cache.reality()
reference = reality["reference"]
st.metric("Bộ đối chiếu gross", reference["status"], f"{reference['pass_rate']:.0%} ô đạt")
st.caption(
    f"{reference['scored']}/{reference['total']} ô có hồ sơ; yêu cầu sai lệch ≤15% ở ≥80% ô. "
    "Ô thiếu hồ sơ vẫn tính trong mẫu số. Dự đoán năm 2026; gross thị trường gần đúng sau hiệu chỉnh."
)
st.dataframe(pd.DataFrame(reference["cells"]), hide_index=True, width="stretch")
for limitation in reality["limitations"]:
    st.caption(limitation)
with st.expander("Mốc mean gross đã dùng fit city: trước/sau role (không kiểm chứng độc lập)"):
    st.dataframe(pd.DataFrame(reality["calibration_cells"]), hide_index=True, width="stretch")
with st.expander("ITviec 2023–2025 đã dùng fit composite vai trò (không kiểm chứng độc lập)"):
    st.dataframe(pd.DataFrame(reality["role_calibration_cells"]), hide_index=True, width="stretch")
with st.expander("ITviec 2025–2026: gross/net chưa xác định, chỉ tham khảo"):
    st.dataframe(pd.DataFrame(reality["unknown_basis_cells"]), hide_index=True, width="stretch")
with st.expander("Vai trò nguồn thay thế: Cloud và QA-QC, chỉ tham khảo"):
    st.dataframe(pd.DataFrame(reality["context_cells"]), hide_index=True, width="stretch")
with st.expander("Giải thích các chỉ số đánh giá mô hình (MAE, RMSE, R², MAPE)"):
    st.markdown("""
    Các chỉ số MAE, RMSE, R² và MAPE được sử dụng để đánh giá
    mức độ chính xác của các mô hình hồi quy trong bài toán
    dự đoán mức lương lập trình viên.

    **1. MAE (Mean Absolute Error - Sai số tuyệt đối trung bình)**

    - Đo lường trung bình độ chênh lệch tuyệt đối giữa mức lương
      dự đoán và mức lương thực tế.
    - Công thức: MAE = trung bình của |Giá trị thực tế - Giá trị dự đoán|.
    - Đơn vị: triệu VND/tháng.
    - MAE càng nhỏ, mô hình dự đoán càng chính xác.
    - Ít nhạy cảm với các giá trị ngoại lai hơn RMSE.

    **Ý nghĩa trong dự án:** Nếu MAE = 2, mô hình dự đoán mức
    lương lệch trung bình khoảng 2 triệu VND/tháng so với thực tế.

    ---

    **2. RMSE (Root Mean Squared Error - Căn bậc hai sai số bình phương trung bình)**

    - Là căn bậc hai của trung bình bình phương sai số dự đoán.
    - Công thức: RMSE = sqrt(mean((y thực tế - y dự đoán)²)).
    - Đơn vị: triệu VND/tháng.
    - RMSE càng nhỏ, mô hình càng tốt.
    - Phạt nặng hơn đối với những dự đoán có sai số lớn.

    **Ý nghĩa trong dự án:** RMSE giúp phát hiện các trường hợp
    mô hình dự đoán mức lương sai lệch quá lớn. Nếu RMSE lớn
    hơn MAE đáng kể, có thể tồn tại một số dự đoán sai nghiêm trọng.

    ---

    **3. R² (R-squared - Hệ số xác định)**

    - Đo lường mức độ mô hình giải thích sự biến động của mức lương
      dựa trên các đặc trưng đầu vào.
    - Công thức: R² = 1 - (Tổng bình phương sai số / Tổng bình
      phương độ lệch so với giá trị trung bình).
    - R² càng gần 1, mô hình càng giải thích tốt biến động dữ liệu.
    - R² = 0: mô hình có hiệu quả tương đương dự đoán bằng giá trị
      trung bình trên tập đánh giá.
    - R² < 0: mô hình có kết quả kém hơn baseline dự đoán trung bình.

    **Ý nghĩa trong dự án:** R² cho biết mô hình giải thích được
    bao nhiêu phần biến động của mức lương trong dữ liệu đánh giá.
    Ví dụ R² = 0.85 tương ứng mức giải thích 85% biến động
    theo cách diễn giải thông thường.

    ---

    **4. MAPE (Mean Absolute Percentage Error - Sai số phần trăm tuyệt đối trung bình)**

    - Đo lường sai số tuyệt đối trung bình dưới dạng phần trăm
      so với mức lương thực tế.
    - Công thức: MAPE = trung bình(|(y thực tế - y dự đoán)
      / y thực tế|) × 100%.
    - Không có đơn vị đo.
    - MAPE càng nhỏ, mô hình càng chính xác.
    - Hạn chế: Không phù hợp khi giá trị thực tế bằng 0 hoặc
      rất gần 0.

    **Ý nghĩa trong dự án:** Nếu MAPE = 10%, mức lương dự đoán
    có sai số phần trăm tuyệt đối trung bình khoảng 10% so với
    mức lương thực tế.

    ---

    **Tổng kết cách sử dụng:**

    | Chỉ số | Mục đích | Giá trị tốt |
    |---|---|---|
    | MAE | Đo sai số trung bình | Càng nhỏ càng tốt |
    | RMSE | Đánh giá và phạt lỗi lớn | Càng nhỏ càng tốt |
    | R² | Đánh giá khả năng giải thích biến động | Càng gần 1 càng tốt |
    | MAPE | Đánh giá sai số theo phần trăm | Càng nhỏ càng tốt |

    **Trong dự án:** Kết hợp cả bốn chỉ số giúp đánh giá mô hình
    toàn diện hơn. MAE được sử dụng làm tiêu chí lựa chọn mô hình
    trên tập validation; RMSE, R² và MAPE cung cấp thêm góc nhìn
    về sai số và khả năng dự đoán.
    """)

