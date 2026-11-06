"""Bộ nhớ đệm Streamlit cho dữ liệu, mô hình và biểu đồ salary-v2."""

import streamlit as st

from . import salary_charts as charts
from .salary_dataset import load_dataset
from .salary_model import MODEL_LABELS, advise, load_report, load_skill_value
from .salary_validation import load_validation
from .salary_visuals import png


@st.cache_data(show_spinner=False, max_entries=1)
def dataset():
    return load_dataset()


@st.cache_data(show_spinner=False, max_entries=1)
def report():
    return load_report()


@st.cache_data(show_spinner=False, max_entries=1)
def skill_value():
    return load_skill_value()


@st.cache_data(show_spinner=False, max_entries=1)
def validation():
    return load_validation()


@st.cache_data(show_spinner=False, max_entries=64)
def chart(name, *args):
    """PNG của một biểu đồ trong salary_charts, tính một lần cho mỗi bộ tham số."""
    frame = dataset()
    builders = {
        "skill_demand": lambda: charts.top_skill_demand(frame),
        "skill_salary": lambda: charts.top_skill_salary(frame),
        "experience": lambda: charts.experience_salary(frame),
        "roles": lambda: charts.role_salary(frame),
        "regions": lambda: charts.region_salary(frame),
        "heatmap": lambda: charts.role_region_heatmap(frame),
        "distribution": lambda: charts.salary_distribution(frame),
        "role_demand": lambda: charts.role_demand(frame),
        "split": lambda: charts.split_by_role(frame),
        "models": lambda: charts.model_comparison(report(), *args),
        "importance": lambda: charts.feature_importance(report()),
        "uplift": lambda: charts.skill_uplift(skill_value()),
        "reliability": lambda: charts.reliability(validation()["calibration"]),
        "bootstrap": lambda: charts.bootstrap_differences(validation()["bootstrap"], MODEL_LABELS),
        "fairness": lambda: charts.fairness_bias(validation()["fairness"][args[0]]),
    }
    return png(builders[name]())


@st.cache_data(show_spinner=False, max_entries=128)
def advice(role, region, years, skills, model_name):
    return advise(
        {"role": role, "region": region, "experience_years": years, "skills": list(skills)},
        model_name=model_name,
    )
