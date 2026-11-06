"""Biểu đồ Matplotlib/Seaborn trên bộ dữ liệu salary-v2, dùng chung cho web và báo cáo."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .salary_dataset import REGIONS, ROLE_ORDER, skill_lists

BLUE = "#2563eb"
GREY = "#cbd5e1"
EXPERIENCE_BINS = [-0.1, 0.9, 1.9, 2.9, 3.9, 4.9, 7.9, 30]
EXPERIENCE_LABELS = ["<1", "1", "2", "3", "4", "5–7", "8+"]
sns.set_theme(style="whitegrid", rc={"axes.spines.top": False, "axes.spines.right": False})


def skill_table(frame):
    exploded = frame.assign(skill=skill_lists(frame)).explode("skill").dropna(subset=["skill"])
    table = exploded.groupby("skill")["salary"].agg(postings="size", median="median")
    return table.reset_index()


def _skill_bar_height(rows):
    return max(5.0, 0.22 * rows + 1.0)


def top_skill_demand(frame, limit=None):
    """Số tin nhắc đến từng kỹ năng; ``limit=None`` vẽ toàn bộ kỹ năng."""
    table = skill_table(frame).sort_values(["postings", "skill"], ascending=[False, True])
    if limit:
        table = table.head(limit)
    figure, axis = plt.subplots(figsize=(7.5, _skill_bar_height(len(table))))
    sns.barplot(data=table, y="skill", x="postings", color=BLUE, ax=axis)
    axis.bar_label(axis.containers[0], padding=3, fontsize=8)
    axis.set(xlabel="Số tin tuyển dụng nhắc đến", ylabel="")
    figure.tight_layout()
    return figure


def top_skill_salary(frame, limit=None, min_postings=30):
    """Trung vị lương theo kỹ năng; kỹ năng dưới ``min_postings`` tin tô xám (ít dữ liệu)."""
    table = skill_table(frame).sort_values(["median", "skill"], ascending=[False, True])
    if limit:
        table = table.head(limit)
    colors = [BLUE if n >= min_postings else GREY for n in table["postings"]]
    figure, axis = plt.subplots(figsize=(7.5, _skill_bar_height(len(table))))
    sns.barplot(
        data=table, y="skill", x="median", hue="skill", palette=colors, legend=False, ax=axis
    )
    axis.axvline(frame["salary"].median(), color="#475569", linestyle="--", linewidth=1)
    for container in axis.containers:
        axis.bar_label(container, fmt="%.1f", padding=3, fontsize=8)
    axis.set(xlabel="Trung vị lương (triệu VND/tháng)", ylabel="")
    figure.tight_layout()
    return figure


def experience_salary(frame):
    data = frame.dropna(subset=["experience_years"]).copy()
    data["Kinh nghiệm (năm)"] = pd.cut(
        data["experience_years"], EXPERIENCE_BINS, labels=EXPERIENCE_LABELS
    )
    figure, axis = plt.subplots(figsize=(7.5, 4.6))
    sns.boxplot(
        data=data,
        x="Kinh nghiệm (năm)",
        y="salary",
        color="#dbeafe",
        showfliers=False,
        ax=axis,
    )
    medians = data.groupby("Kinh nghiệm (năm)", observed=False)["salary"].median()
    axis.plot(range(len(medians)), medians.to_numpy(), color=BLUE, marker="o", linewidth=2)
    correlation = data[["experience_years", "salary"]].corr(method="spearman").iloc[0, 1]
    axis.set(ylabel="Lương (triệu VND/tháng)")
    axis.set_title(f"Hệ số tương quan Spearman ρ = {correlation:.2f}", fontsize=10)
    figure.tight_layout()
    return figure


def role_salary(frame):
    """Mọi vai trò trong dữ liệu, sắp theo trung vị lương."""
    order = frame.groupby("role")["salary"].median().sort_values(ascending=False).index.tolist()
    counts = frame["role"].value_counts()
    figure, axis = plt.subplots(figsize=(8.5, max(5, len(order) * 0.36)))
    sns.boxplot(
        data=frame,
        y="role",
        x="salary",
        order=order,
        color="#dbeafe",
        showfliers=False,
        ax=axis,
    )
    medians = frame.groupby("role")["salary"].median().reindex(order)
    axis.scatter(medians, range(len(order)), color=BLUE, zorder=3, s=18)
    axis.set_yticks(range(len(order)), [f"{role} (n={counts[role]})" for role in order])
    axis.set(xlabel="Lương (triệu VND/tháng)", ylabel="")
    figure.tight_layout()
    return figure


def region_salary(frame):
    order = [region for region in REGIONS if region in set(frame["region"])]
    table = frame.groupby("region")["salary"].agg(["median", "size"]).reindex(order)
    figure, axis = plt.subplots(figsize=(7.5, 4))
    sns.barplot(x=table.index, y=table["median"], color=BLUE, ax=axis)
    axis.bar_label(
        axis.containers[0],
        labels=[f"{m:.1f}\n(n={n})" for m, n in zip(table["median"], table["size"])],
        fontsize=8,
    )
    axis.set(xlabel="", ylabel="Trung vị lương (triệu VND/tháng)")
    axis.set_ylim(0, table["median"].max() * 1.25)
    figure.tight_layout()
    return figure


def role_region_heatmap(frame, min_postings=3):
    table = frame.pivot_table(index="role", columns="region", values="salary", aggfunc="median")
    counts = frame.pivot_table(index="role", columns="region", values="salary", aggfunc="size")
    table = table.where(counts >= min_postings)
    order = [role for role in ROLE_ORDER if role in table.index]
    columns = [region for region in REGIONS if region in table.columns]
    table = table.reindex(index=order, columns=columns)
    figure, axis = plt.subplots(figsize=(8.5, max(5, len(order) * 0.36)))
    sns.heatmap(
        table,
        annot=True,
        fmt=".0f",
        cmap="Blues",
        linewidths=0.5,
        cbar_kws={"label": "Trung vị lương (triệu)"},
        ax=axis,
    )
    axis.set(xlabel="", ylabel="")
    figure.tight_layout()
    return figure


def salary_distribution(frame):
    figure, axis = plt.subplots(figsize=(7.5, 4))
    sns.histplot(frame["salary"], bins=40, color=BLUE, ax=axis)
    axis.axvline(frame["salary"].median(), color="#0f172a", linestyle="--", linewidth=1)
    axis.set(xlabel="Lương (triệu VND/tháng)", ylabel="Số tin")
    figure.tight_layout()
    return figure


def role_demand(frame):
    counts = frame["role"].value_counts()
    figure, axis = plt.subplots(figsize=(8.5, max(5, len(counts) * 0.32)))
    sns.barplot(x=counts.to_numpy(), y=counts.index, color=BLUE, ax=axis)
    axis.bar_label(axis.containers[0], padding=3, fontsize=8)
    axis.set(xlabel="Số tin có công bố lương", ylabel="")
    figure.tight_layout()
    return figure


def split_by_role(frame):
    table = pd.crosstab(frame["role"], frame["split"])[["train", "valid", "test"]]
    table = table.loc[table.sum(axis=1).sort_values().index]
    figure, axis = plt.subplots(figsize=(8.5, max(5, len(table) * 0.32)))
    table.plot.barh(stacked=True, color=[BLUE, "#60a5fa", "#bfdbfe"], ax=axis, width=0.75)
    axis.set(xlabel="Số tin", ylabel="")
    axis.legend(title="Tập", frameon=False)
    figure.tight_layout()
    return figure


def model_comparison(report, part="test"):
    rows = [
        {"Mô hình": values["label"], "MAE": values[part]["MAE"], "RMSE": values[part]["RMSE"]}
        for values in report["models"].values()
    ]
    table = pd.DataFrame(rows).melt("Mô hình", var_name="Chỉ số", value_name="Triệu VND")
    figure, axis = plt.subplots(figsize=(8, 4))
    sns.barplot(
        data=table,
        x="Mô hình",
        y="Triệu VND",
        hue="Chỉ số",
        palette=[BLUE, "#93c5fd"],
        ax=axis,
    )
    for container in axis.containers:
        axis.bar_label(container, fmt="%.2f", fontsize=8)
    axis.set(xlabel="")
    axis.legend(frameon=False)
    figure.tight_layout()
    return figure


def actual_vs_predicted(predictions):
    figure, axis = plt.subplots(figsize=(6, 5))
    axis.scatter(predictions["salary"], predictions["predicted"], s=10, alpha=0.45, color=BLUE)
    limit = max(predictions["salary"].max(), predictions["predicted"].max()) * 1.05
    axis.plot([0, limit], [0, limit], color="#0f172a", linestyle="--", linewidth=1)
    axis.set(
        xlim=(0, limit),
        ylim=(0, limit),
        xlabel="Lương thực tế (triệu VND/tháng)",
        ylabel="Lương dự đoán (triệu VND/tháng)",
    )
    figure.tight_layout()
    return figure


def feature_importance(report, limit=15):
    series = pd.Series(report["permutation_importance"]).head(limit)
    series.index = [name.replace("skill::", "Kỹ năng: ") for name in series.index]
    figure, axis = plt.subplots(figsize=(7.5, 5))
    sns.barplot(x=series.to_numpy(), y=series.index, color=BLUE, ax=axis)
    axis.set(xlabel="Mức giảm R² khi xáo trộn đặc trưng (tập valid)", ylabel="")
    figure.tight_layout()
    return figure


def skill_uplift(table, limit=15):
    table = table.nlargest(limit, "model_uplift")
    figure, axis = plt.subplots(figsize=(7.5, 5))
    colors = [BLUE if value > 0 else GREY for value in table["model_uplift"]]
    sns.barplot(data=table, y="skill", x="model_uplift", palette=colors, hue="skill", ax=axis)
    axis.bar_label(axis.containers[0], fmt="%+.2f", padding=3, fontsize=8)
    for container in axis.containers[1:]:
        axis.bar_label(container, fmt="%+.2f", padding=3, fontsize=8)
    axis.set(xlabel="Mức tăng lương dự đoán khi bổ sung kỹ năng (triệu VND/tháng)", ylabel="")
    figure.tight_layout()
    return figure


def error_by_role(predictions):
    table = predictions.groupby("role")["abs_error"].mean().sort_values()
    figure, axis = plt.subplots(figsize=(8, max(5, len(table) * 0.32)))
    sns.barplot(x=table.to_numpy(), y=table.index, color=BLUE, ax=axis)
    axis.set(xlabel="MAE trên tập test (triệu VND/tháng)", ylabel="")
    figure.tight_layout()
    return figure


def recommendation_chart(recommendations):
    table = pd.DataFrame(recommendations)
    figure, axis = plt.subplots(figsize=(6.5, 3.2))
    colors = [BLUE if value > 0 else GREY for value in table["uplift"]]
    axis.barh(table["skill"][::-1], table["uplift"][::-1], color=colors[::-1])
    axis.axvline(0, color="#0f172a", linewidth=0.8)
    axis.set(xlabel="Thay đổi lương dự đoán (triệu VND/tháng)")
    figure.tight_layout()
    return figure


def experience_path_chart(path):
    table = pd.DataFrame(path)
    figure, axis = plt.subplots(figsize=(6.5, 3.2))
    axis.plot(table["experience_years"], table["salary"], marker="o", color=BLUE, linewidth=2)
    for row in table.itertuples():
        axis.annotate(
            f"{row.salary:.1f}\n{row.level}",
            (row.experience_years, row.salary),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
        )
    axis.set(xlabel="Số năm kinh nghiệm", ylabel="Triệu VND/tháng")
    axis.set_ylim(0, table["salary"].max() * 1.3)
    axis.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    figure.tight_layout()
    return figure


def close(figure):
    plt.close(figure)


def summary(frame):
    return {
        "postings": len(frame),
        "companies": int(frame["company_key"].nunique()),
        "roles": int(frame["role"].nunique()),
        "median": float(frame["salary"].median()),
        "mean": float(frame["salary"].mean()),
        "p90": float(np.quantile(frame["salary"], 0.9)),
    }


def reliability(calibration):
    table = pd.DataFrame(calibration["reliability"])
    figure, axis = plt.subplots(figsize=(6, 5))
    axis.plot(
        [0, 1], [0, 1], color="#475569", linestyle="--", linewidth=1, label="Hiệu chuẩn hoàn hảo"
    )
    axis.plot(
        table["level"], table["coverage"], marker="o", color=BLUE, label="Mô hình trên tập test"
    )
    axis.set(
        xlim=(0, 1),
        ylim=(0, 1),
        xlabel="Mức tin cậy danh nghĩa của khoảng",
        ylabel="Tỉ lệ tin thật nằm trong khoảng",
    )
    axis.legend(frameon=False, loc="upper left")
    figure.tight_layout()
    return figure


def bootstrap_differences(bootstrap, labels):
    figure, axis = plt.subplots(figsize=(7.5, 4))
    colors = [BLUE, "#60a5fa", "#94a3b8"]
    for color, (name, values) in zip(colors, bootstrap["differences"].items()):
        if name == "Baseline":
            continue
        sns.histplot(
            values["samples"], bins=40, color=color, alpha=0.55, ax=axis, label=labels[name]
        )
    axis.axvline(0, color="#0f172a", linewidth=1)
    axis.set(
        xlabel="MAE Gradient Boosting − MAE mô hình khác (triệu VND/tháng)",
        ylabel="Số lần bootstrap",
    )
    axis.legend(frameon=False)
    figure.tight_layout()
    return figure


def fairness_bias(group):
    rows = [row for row in group["groups"] if row["enough"]]
    table = pd.DataFrame(rows).sort_values("bias_pct")
    figure, axis = plt.subplots(figsize=(7.5, max(3, len(table) * 0.45)))
    low = table["bias_pct"] - table["bias_pct_ci95"].map(lambda ci: ci[0])
    high = table["bias_pct_ci95"].map(lambda ci: ci[1]) - table["bias_pct"]
    axis.errorbar(
        table["bias_pct"], range(len(table)), xerr=[low, high], fmt="o", color=BLUE, capsize=3
    )
    axis.axvline(0, color="#0f172a", linewidth=1)
    axis.set_yticks(range(len(table)), [f"{g} (n={n})" for g, n in zip(table["group"], table["n"])])
    axis.set(xlabel="Độ lệch trung bình (dự đoán − thật) / thật, % — khoảng tin cậy 95%", ylabel="")
    figure.tight_layout()
    return figure
