"""So sánh các mô hình salary-v2 đã lưu. Trang này không huấn luyện lại."""

import pandas as pd
import streamlit as st

from career_market import salary_app
from career_market import salary_charts as charts
from career_market.salary_model import artifacts_dir
from career_market.salary_visuals import png

st.title("Đánh giá mô hình")
report = salary_app.report()
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
predictions = pd.read_csv(artifacts_dir() / "test_predictions.csv")
left, right = st.columns(2, gap="medium")
with left, st.container(border=True):
    st.subheader("Thực tế và dự đoán (tập test)")
    st.image(png(charts.actual_vs_predicted(predictions)), width="stretch")
with right, st.container(border=True):
    st.subheader("Mức độ quan trọng của đặc trưng")
    st.image(salary_app.chart("importance"), width="stretch")
left, right = st.columns(2, gap="medium")
with left, st.container(border=True):
    st.subheader("Kỹ năng mang lại giá trị gia tăng thu nhập")
    st.caption("Mức tăng lương dự đoán trung bình khi bổ sung kỹ năng, các yếu tố khác giữ nguyên")
    st.image(salary_app.chart("uplift"), width="stretch")
with right, st.container(border=True):
    st.subheader("Sai số theo vai trò (tập test)")
    st.image(png(charts.error_by_role(predictions)), width="stretch")
with st.expander("Kết quả dò siêu tham số trên tập valid"):
    for name, trials in report["tuning"].items():
        st.write(f"**{report['models'][name]['label']}**")
        st.dataframe(pd.DataFrame(trials), hide_index=True, width="stretch")
