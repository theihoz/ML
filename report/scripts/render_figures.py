"""Vẽ lại toàn bộ biểu đồ dữ liệu của báo cáo từ code và artifact salary-v2.

Ảnh biểu đồ không lưu trong git: chạy script này trước build_report.js / build_slides.js.
Ảnh chụp giao diện (ui-*.png) và sơ đồ (report/diagrams) không sinh từ dữ liệu nên giữ nguyên.

    PYTHONPATH=job_market/src job_market/.venv/bin/python report/scripts/render_figures.py
"""

import sys
from pathlib import Path

import pandas as pd

from career_market import salary_charts as charts
from career_market.salary_dataset import load_dataset
from career_market.salary_model import MODEL_LABELS, artifacts_dir, load_report, load_skill_value
from career_market.salary_validation import load_validation
from career_market.salary_visuals import png

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "report" / "figures"


def builders():
    frame = load_dataset()
    report = load_report()
    validation = load_validation()
    predictions = pd.read_csv(artifacts_dir() / "test_predictions.csv")
    fairness = validation["fairness"]
    return {
        "split": lambda: charts.split_by_role(frame),
        "distribution": lambda: charts.salary_distribution(frame),
        "role_demand": lambda: charts.role_demand(frame),
        "skill_demand": lambda: charts.top_skill_demand(frame),
        "skill_salary": lambda: charts.top_skill_salary(frame),
        "experience": lambda: charts.experience_salary(frame),
        "roles": lambda: charts.role_salary(frame),
        "regions": lambda: charts.region_salary(frame),
        "heatmap": lambda: charts.role_region_heatmap(frame),
        "models_test": lambda: charts.model_comparison(report, "test"),
        "actual_pred": lambda: charts.actual_vs_predicted(predictions),
        "error_role": lambda: charts.error_by_role(predictions),
        "importance": lambda: charts.feature_importance(report),
        "uplift": lambda: charts.skill_uplift(load_skill_value()),
        "reliability": lambda: charts.reliability(validation["calibration"]),
        "bootstrap": lambda: charts.bootstrap_differences(validation["bootstrap"], MODEL_LABELS),
        "fair_level": lambda: charts.fairness_bias(fairness["level"]),
        "fair_platform": lambda: charts.fairness_bias(fairness["platform"]),
        "fair_region": lambda: charts.fairness_bias(fairness["region"]),
    }


def main(output=FIGURES):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, build in builders().items():
        (output / f"{name}.png").write_bytes(png(build()))
        print(output / f"{name}.png")


if __name__ == "__main__":
    main(*sys.argv[1:])
