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
a, b, c = st.columns(3)
a.metric("Mô hình đang dùng", report["chosen_model"])
b.metric("Tin dùng huấn luyện", report["counts"]["train"])
c.metric("Tin dùng kiểm tra", report["counts"]["test"])
st.caption("Bản thử nghiệm từ 14 tin / 11 công ty. Sai số càng thấp càng tốt.")
part = st.radio(
    "Đánh giá trên",
    ["test", "validation"],
    format_func=lambda v: "Tập kiểm tra" if v == "test" else "Tập chọn mô hình",
    horizontal=True,
)
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
sns.barplot(data=table, x="Mô hình", y="Sai số trung bình", color="#247f8c", ax=axis)
axis.set_ylabel("Triệu đồng / tháng")
axis.set_xlabel("")
sns.despine(ax=axis)
figure.tight_layout()
st.pyplot(figure)
plt.close(figure)
st.dataframe(table, hide_index=True, use_container_width=True)
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
