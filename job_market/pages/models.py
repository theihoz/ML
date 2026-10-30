"""Simple comparison of the saved models. Never starts training."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from career_market import MarketError, MarketService

st.title("So sánh mô hình")
try:
    audit = MarketService().audit_training_run()
except MarketError as error:
    st.info(str(error))
    st.stop()
report = audit["report"]
selected_model = st.selectbox(
    "Mô hình",
    ["Ridge", "LinearRegression"],
    format_func=lambda name: "Linear Regression" if name == "LinearRegression" else name,
    key="compare_model",
)
part = st.radio(
    "Đánh giá trên",
    ["test", "validation"],
    format_func=lambda value: "Tập kiểm tra" if value == "test" else "Tập chọn mô hình",
    horizontal=True,
    key="compare_part",
)
selected_scores = report["metrics"][selected_model][part]
a, b, c = st.columns(3)
a.metric("Mô hình đang xem", selected_model)
b.metric("Sai số trung bình", f"{selected_scores['MAE'] / 1e6:.2f}")
c.metric("Sai số RMSE", f"{selected_scores['RMSE'] / 1e6:.2f}")
st.caption(
    f"{report['source_entities']} tin / {report['company_count']} công ty · {selected_scores['n']} tin đánh giá · triệu đồng/tháng"
)
if st.button("Dự đoán với mô hình này", type="primary"):
    chosen_inputs = dict(
        st.session_state.get("salary_last_inputs", {"role": "Data/ML", "city": "HN"})
    )
    chosen_inputs["model"] = selected_model
    st.session_state["salary_last_inputs"] = chosen_inputs
    st.session_state.pop("salary_model", None)
    st.session_state.pop("salary_estimate", None)
    st.switch_page("pages/predict.py")
rows = []
for name, parts in report["metrics"].items():
    score = parts[part]
    rows.append(
        {
            "Mô hình": "Mốc trung vị" if name == "train_median_baseline" else name,
            "Sai số trung bình": score["MAE"] / 1e6,
            "Sai số RMSE": score["RMSE"] / 1e6,
            "Số tin": score["n"],
        }
    )
table = pd.DataFrame(rows)
figure, axis = plt.subplots(figsize=(9, 3.8))
sns.barplot(
    data=table,
    x="Mô hình",
    y="Sai số trung bình",
    hue="Mô hình",
    palette={name: "#2563eb" if name == selected_model else "#cbd5e1" for name in table["Mô hình"]},
    legend=False,
    ax=axis,
)
axis.set_ylabel("Triệu đồng / tháng")
axis.set_xlabel("")
sns.despine(ax=axis)
figure.tight_layout()
st.pyplot(figure)
plt.close(figure)
st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    column_config={
        "Sai số trung bình": st.column_config.NumberColumn(format="%.2f"),
        "Sai số RMSE": st.column_config.NumberColumn(format="%.2f"),
    },
)
st.caption(
    "Đơn vị: triệu đồng/tháng. Ridge được chọn bằng tập chọn mô hình, không chọn theo kết quả kiểm tra."
)
st.download_button("Tải kết quả", table.to_csv(index=False), "so-sanh-mo-hinh.csv", "text/csv")
with st.expander("Dữ liệu và thông tin kiểm chứng"):
    st.write(
        "Chia theo công ty: 10 tin học, 2 tin chọn mô hình, 2 tin kiểm tra. Chưa có kinh nghiệm theo năm được xác minh."
    )
    st.write(
        "Nạp lại model: "
        + ("khớp kết quả đã lưu" if audit["reload_check"]["consistent"] else "không khớp")
    )
    st.dataframe(audit["split"]["membership"], hide_index=True)
    st.json(audit["review_addendum"])
