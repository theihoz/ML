"""Read the persisted run. No training trigger is exposed in Streamlit."""

import json

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from career_market import MarketError, MarketService

st.title("Kết quả huấn luyện ngoại tuyến")
st.caption("Trang này chỉ nạp run đã lưu; mở trang hoặc upload không huấn luyện model.")
try:
    audit = MarketService().audit_training_run()
except MarketError as error:
    st.info(str(error))
    st.stop()
report = audit["report"]
st.warning(
    "Run thăm dò nhỏ: 14 tin / 11 công ty; validation và test mỗi tập chỉ 2 tin. Không suy rộng thành độ chính xác trên thị trường."
)
left, middle, right = st.columns(3)
left.metric("Model chọn bằng validation", report["chosen_model"])
middle.metric(
    "Test MAE · triệu VND/tháng",
    f"{report['metrics'][report['chosen_model']]['test']['MAE'] / 1e6:.2f}",
)
right.metric("Nạp lại model", "Khớp" if audit["reload_check"]["consistent"] else "Lỗi")
st.write(
    "Cohort: VND/tháng · gross/net chưa rõ · chưa xác nhận cấu phần lương. Không trộn với hai tin thu nhập YODY."
)
st.write(
    "Đạt tiêu chí so baseline."
    if report["promoted"]
    else "Chưa đạt tiêu chí phát hành; giữ báo cáo, không kích hoạt tư vấn."
)
st.warning(
    "0/14 tin có số năm kinh nghiệm được xác minh; kỹ năng chỉ lấy từ tiêu đề. Run chưa chứng minh tác động của kinh nghiệm hoặc lợi ích khi học kỹ năng."
)
rows = []
for model, parts in report["metrics"].items():
    for part, scores in parts.items():
        rows.append(
            {
                "model": model,
                "split": part,
                "n": scores["n"],
                "MAE triệu VND/tháng": scores["MAE"] / 1e6,
                "RMSE triệu VND/tháng": scores["RMSE"] / 1e6,
            }
        )
table = pd.DataFrame(rows)
st.dataframe(table, hide_index=True)
figure, axis = plt.subplots(figsize=(9, 4))
sns.barplot(
    data=table[table["split"] != "train"], x="model", y="MAE triệu VND/tháng", hue="split", ax=axis
)
axis.set_title("MAE trên validation và test · mỗi tập n=2")
figure.tight_layout()
st.pyplot(figure)
plt.close(figure)
st.subheader("Phân hoạch theo công ty")
st.json(
    {
        "counts": report["counts"],
        "actual_ratios": report["actual_ratios"],
        "cohort": report["cohort"],
    }
)
st.dataframe(audit["split"]["membership"], hide_index=True)
st.download_button("Tải metric CSV", table.to_csv(index=False), "training-metrics.csv", "text/csv")
st.download_button(
    "Tải báo cáo JSON",
    json.dumps(report, ensure_ascii=False, indent=2),
    "training-report.json",
    "application/json",
)
with st.expander("Đối chiếu artifact và dự đoán"):
    st.json(audit["reload_check"])
    st.json(audit["review_addendum"])
    st.json(report)
    st.dataframe(audit["predictions"], hide_index=True)
