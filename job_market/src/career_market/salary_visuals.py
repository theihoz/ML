"""Matplotlib/Seaborn charts with model estimates and observed salaries kept separate."""

import io
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

CITY_NAMES = {"HN": "Hà Nội", "HCM": "TP. Hồ Chí Minh", "Đà Nẵng": "Đà Nẵng"}


def png(figure):
    output = io.BytesIO()
    figure.tight_layout()
    figure.savefig(output, format="png", dpi=140, bbox_inches="tight")
    plt.close(figure)
    return output.getvalue()


def scenarios(service, role, city, model_name=None):
    chosen = service.estimate_salary(role, city, model_name=model_name)
    if chosen["status"] != "ok":
        return {"status": chosen["status"], "table": [], "png": None}
    table = []
    for place in CITY_NAMES:
        estimate = service.estimate_salary(chosen["role"], place, model_name=chosen["model"])
        if estimate["status"] == "ok":
            table.append(
                {
                    "city": place,
                    "salary_vnd_month": estimate["salary_vnd_month"],
                    "selected": place == chosen["location"],
                }
            )
    figure, axis = plt.subplots(figsize=(9, 3.1))
    values = [row["salary_vnd_month"] / 1e6 for row in table]
    bars = axis.barh(
        [CITY_NAMES[row["city"]] for row in table],
        values,
        color=["#2563eb" if row["selected"] else "#cbdafa" for row in table],
    )
    axis.bar_label(bars, labels=[f"{value:.1f}" for value in values], padding=5)
    axis.set_xlim(0, max(values) * 1.2)
    axis.set_xlabel("Triệu đồng / tháng")
    axis.invert_yaxis()
    sns.despine(ax=axis, left=True)
    return {"status": "ok", "table": table, "png": png(figure), "kind": "model_estimates"}


def mean_table(rows, field):
    buckets = defaultdict(dict)
    for row in rows:
        values = [row[field]] if isinstance(row[field], str) else row[field]
        for value in set(values):
            buckets[value][row["posting_id"]] = row["salary_target_vnd_month"]
    return sorted(
        [
            {
                "name": name,
                "posting_count": len(values),
                "mean_vnd_month": sum(values.values()) / len(values),
            }
            for name, values in buckets.items()
        ],
        key=lambda r: (-r["mean_vnd_month"], r["name"]),
    )


def mean_chart(table, title):
    if not table:
        return None
    frame = pd.DataFrame(
        [
            {
                "Nhóm": f"{row['name']} (n={row['posting_count']})",
                "Triệu đồng / tháng": row["mean_vnd_month"] / 1e6,
            }
            for row in table
        ]
    )
    figure, axis = plt.subplots(figsize=(8, max(3, len(table) * 0.45)))
    sns.barplot(data=frame, y="Nhóm", x="Triệu đồng / tháng", color="#2563eb", ax=axis)
    axis.set_title(title)
    axis.set_ylabel("")
    sns.despine(ax=axis)
    return png(figure)


def salary_analysis(service, cohort, charts=None):
    if cohort == "salary":
        # Current raw evidence review for EDA, not a rewrite of the frozen model dataset.
        rows = service.adjudicate_training_labels()["rows"]
        scope = "salary_components_unspecified"
    elif cohort == "income":
        rows = service.prepare()["targets"]
        scope = "advertised_monthly_income"
    else:
        raise ValueError("Nhóm dữ liệu lương không hợp lệ.")
    return analyze_rows(rows, scope, charts)


def analyze_rows(rows, scope, charts=None):
    requested = set(charts) if charts is not None else {"roles", "regions", "skills", "experience"}
    if not requested.issubset({"roles", "regions", "skills", "experience"}):
        raise ValueError("Biểu đồ yêu cầu không hợp lệ.")
    quantity = "thu nhập" if scope == "advertised_monthly_income" else "lương"
    rows = [
        row
        for row in rows
        if row.get("salary_currency") == "VND"
        and row.get("salary_period") == "MONTH"
        and row.get("salary_basis") == "unknown"
        and row.get("compensation_scope") == scope
    ]
    rows = list({row["posting_id"]: row for row in rows}.values())
    tables = {
        "roles": mean_table(rows, "role"),
        "regions": mean_table(rows, "locations"),
        "skills": mean_table(rows, "skills"),
    }
    experience = [
        {
            "posting_id": row["posting_id"],
            "title": row["title_raw"],
            "experience_min": row["experience_min"],
            "experience_max": row["experience_max"],
            "salary_vnd_month": row["salary_target_vnd_month"],
        }
        for row in rows
        if row.get("experience_min") is not None and row.get("experience_max") is not None
    ]
    chart = None
    if experience and "experience" in requested:
        figure, axis = plt.subplots(figsize=(8, 3.5))
        for row in experience:
            low, high = row["experience_min"], row["experience_max"]
            axis.errorbar(
                (low + high) / 2,
                row["salary_vnd_month"] / 1e6,
                xerr=(high - low) / 2,
                fmt="o",
                capsize=5,
                label=row["title"],
            )
        axis.set_xlabel("Số năm kinh nghiệm yêu cầu")
        axis.set_ylabel("Triệu đồng / tháng")
        axis.legend()
        sns.despine(ax=axis)
        chart = png(figure)
    return {
        "posting_count": len(rows),
        "cohort": scope,
        "quantity": quantity,
        "mean_vnd_month": sum(row["salary_target_vnd_month"] for row in rows) / len(rows)
        if rows
        else None,
        **tables,
        "experience": experience,
        "charts": {
            "roles": mean_chart(tables["roles"], f"Trung điểm {quantity} theo nghề")
            if "roles" in requested
            else None,
            "regions": mean_chart(tables["regions"], f"Trung điểm {quantity} theo khu vực")
            if "regions" in requested
            else None,
            "skills": mean_chart(
                tables["skills"], f"Trung điểm {quantity} trong tin có nhắc kỹ năng"
            )
            if "skills" in requested
            else None,
            "experience": chart,
        },
    }
