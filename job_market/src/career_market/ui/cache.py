"""Bộ nhớ đệm Streamlit.

Mục này làm gì: nạp dữ liệu, báo cáo mô hình và vẽ biểu đồ đúng một lần, các trang chỉ gọi lại.
"""

import streamlit as st

from ..data.dataset import load_dataset
from ..model.advisor import advise
from ..model.estimators import MODEL_LABELS
from ..model.reality import reality_check
from ..model.training import load_report, load_skill_value
from ..model.validation import load_validation
from . import charts
from .charts import png


@st.cache_data(show_spinner=False, max_entries=1)
def dataset():
    """Bộ dữ liệu, đọc một lần cho cả app."""
    return load_dataset()


@st.cache_data(show_spinner=False, max_entries=1)
def report():
    """Báo cáo huấn luyện của mô hình đang phục vụ."""
    return load_report()


@st.cache_data(show_spinner=False, max_entries=1)
def skill_value():
    """Bảng giá trị gia tăng của kỹ năng."""
    return load_skill_value()


@st.cache_data(show_spinner=False, max_entries=1)
def validation():
    """Kết quả kiểm định (độ tin cậy, công bằng, chuẩn production)."""
    return load_validation()


@st.cache_data(show_spinner=False, max_entries=64)
def chart(name, *args):
    """PNG của một biểu đồ trong ui/charts.py, tính một lần cho mỗi bộ tham số."""
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


@st.cache_data(show_spinner=False, max_entries=64)
def market_chart(name, sources, roles, regions):
    """Biểu đồ kỹ năng trên phần dữ liệu đã lọc (trang Thị trường)."""
    frame = filter_postings(dataset(), sources, roles, regions)
    if name == "demand":
        return png(charts.top_skill_demand(frame, limit=20))
    return png(charts.top_skill_salary(frame, limit=20, min_postings=10))


def filter_postings(frame, sources, roles, regions):
    """Lọc tin theo nguồn/vai trò/khu vực; danh sách rỗng nghĩa là không lọc."""
    mask = frame["source"].isin(sources) if sources else True
    if roles:
        mask &= frame["role"].isin(roles)
    if regions:
        mask &= frame["region"].isin(regions)
    return frame[mask] if mask is not True else frame


@st.cache_data(show_spinner=False, max_entries=128)
def advice(
    role,
    region,
    years,
    skills,
    model_name,
    level=None,
    title="",
    company_type="Khác",
    work_mode="Không rõ",
):
    """Kết quả tư vấn cho một hồ sơ; cùng hồ sơ thì không tính lại."""
    return advise(
        {
            "role": role,
            "region": region,
            "experience_years": years,
            "skills": list(skills),
            "level": level,
            "title": title,
            "company_type": company_type,
            "work_mode": work_mode,
        },
        model_name=model_name,
    )


@st.cache_data(show_spinner=False, max_entries=1)
def reality():
    """Kết quả so với báo cáo lương bên ngoài."""
    return reality_check()
