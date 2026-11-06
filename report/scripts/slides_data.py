"""Gom số liệu cho slide thuyết trình từ dữ liệu và artifact salary-v2.

Chạy từ thư mục job_market: PYTHONPATH=src python ../report/scripts/slides_data.py <output.json>
"""

import json
import sys

import pandas as pd

from career_market.salary_charts import EXPERIENCE_BINS, EXPERIENCE_LABELS, skill_table
from career_market.salary_dataset import data_root, load_dataset
from career_market.salary_model import load_report, load_skill_value
from career_market.salary_validation import load_validation

frame = load_dataset()
report = load_report()
validation = load_validation()
raw = pd.read_csv(data_root() / "raw/vietnam_it_job_posts_v1.csv")
posted = raw[raw["source_platform"].isin(["itviec", "topcv", "careerviet"])]
years = posted["posted_at"].str[:4].dropna()
experience = frame.groupby(
    pd.cut(frame["experience_years"], EXPERIENCE_BINS, labels=EXPERIENCE_LABELS), observed=False
)["salary"].median()
skills = skill_table(frame)
roles = frame.groupby("role")["salary"].median().sort_values(ascending=False)
data = {
    "posted_years": years[years < "2026"].value_counts().sort_index().to_dict(),
    "experience": {str(k): round(float(v), 1) for k, v in experience.items()},
    "top_demand": skills.nlargest(8, "postings")[["skill", "postings"]].to_dict("records"),
    "top_salary": skills[skills["postings"] >= 30]
    .nlargest(8, "median")[["skill", "median"]]
    .to_dict("records"),
    "roles": {k: round(float(v), 1) for k, v in roles.items()},
    "models": {
        name: {
            "label": values["label"],
            **{part: {k: values[part][k] for k in ("MAE", "RMSE", "R2", "MAPE")} for part in ("train", "valid", "test")},
        }
        for name, values in report["models"].items()
    },
    "uplift": load_skill_value().head(8)[["skill", "model_uplift"]].to_dict("records"),
    "calibration": validation["calibration"],
    "bootstrap": {
        "models": validation["bootstrap"]["models"],
        "differences": {
            k: {key: v[key] for key in ("mean", "ci95", "p_better")}
            for k, v in validation["bootstrap"]["differences"].items()
        },
        "companies": validation["bootstrap"]["companies"],
        "rounds": validation["bootstrap"]["rounds"],
    },
    "fairness": {
        key: [g for g in validation["fairness"][key]["groups"] if g["enough"]]
        for key in ("region", "level", "platform")
    },
    "gender": {k: validation["gender"][k] for k in ("counts", "mentioned", "share_pct")},
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(data, handle, ensure_ascii=False, indent=1)
print("ok")
