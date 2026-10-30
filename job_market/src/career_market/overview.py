"""Overview assembled from verified observations, not illustrative market figures."""

from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .salary_visuals import analyze_rows, png


def market_overview(service):
    prepared = service.prepare()
    postings = list({row["posting_id"]: row for row in prepared["eda"]}.values())
    demand = service.skill_demand(postings, limit=10)
    salary = service.salary_analysis("salary", charts=("roles",))
    income = analyze_rows(prepared["targets"], "advertised_monthly_income", charts=("experience",))
    counts = Counter()
    for row in postings:
        places = set(row["locations"])
        if len(places) > 1:
            group = "Nhiều địa điểm"
        elif places == {"HN"}:
            group = "Hà Nội"
        elif places == {"HCM"}:
            group = "TP. Hồ Chí Minh"
        elif places:
            group = "Khu vực khác"
        else:
            group = "Chưa rõ"
        counts[group] += 1
    regions = [{"name": name, "posting_count": count} for name, count in counts.most_common()]
    figure, axis = plt.subplots(figsize=(7, 3.8))
    if demand["table"]:
        frame = pd.DataFrame(demand["table"])
        sns.barplot(data=frame, y="skill", x="posting_count", color="#2563eb", ax=axis)
        axis.set_xlabel("Số tin tuyển dụng")
        axis.set_ylabel("")
    else:
        axis.text(0.5, 0.5, "Chưa có kỹ năng", ha="center", va="center")
        axis.set_axis_off()
    sns.despine(ax=axis)
    skills_png = png(figure)
    figure, axis = plt.subplots(figsize=(7, 3.8))
    if regions:
        wedges, _ = axis.pie(
            [row["posting_count"] for row in regions],
            startangle=90,
            colors=["#2563eb", "#8b5cf6", "#10b981", "#f59e0b", "#cbd5e1"],
            wedgeprops={"width": 0.32, "edgecolor": "white"},
        )
        axis.text(
            0,
            0,
            str(len(postings)),
            ha="center",
            va="center",
            fontsize=22,
            fontweight="bold",
            color="#1e293b",
        )
        axis.legend(
            wedges,
            [f"{row['name']} · {row['posting_count']}" for row in regions],
            loc="center left",
            bbox_to_anchor=(1, 0.5),
            frameon=False,
        )
    regions_png = png(figure)
    return {
        "posting_count": len(postings),
        "salary_posting_count": salary["posting_count"],
        "mean_salary_vnd_month": salary["mean_vnd_month"],
        "top_skills": [row["skill"] for row in demand["table"][:3]],
        "source_count": len(prepared["sources"]) + 1,
        "model_count": len(
            [
                name
                for name in service.audit_training_run()["report"]["metrics"]
                if name != "train_median_baseline"
            ]
        ),
        "regions": regions,
        "remote_count": sum("Remote" in row["work_modes"] for row in postings),
        "experience_posting_count": len(income["experience"]),
        "charts": {
            "skills": skills_png,
            "roles": salary["charts"]["roles"],
            "regions": regions_png,
            "experience": income["charts"]["experience"],
        },
    }
