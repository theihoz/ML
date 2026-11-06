"""Independent, anonymized salary observations; never used for model fitting."""

import math

import pandas as pd

from ..data.rules import LEVELS, REGIONS, ROLE_ORDER, SKILLS
from ..paths import data_root
from .advisor import advise
from .estimators import CURRENT_YEAR

COLUMNS = {"role", "level", "region", "experience_years", "skills", "gross_salary", "year"}


def _number(row, field, number):
    try:
        value = float(row[field])
    except (TypeError, ValueError):
        raise ValueError(f"Dòng {number}: {field} phải là số hữu hạn.") from None
    if not math.isfinite(value):
        raise ValueError(f"Dòng {number}: {field} phải là số hữu hạn.")
    return value


def score_golden(path=None, model_name=None):
    frame = pd.read_csv(
        path or data_root() / "reference" / "golden_profiles.csv", dtype=str, keep_default_na=False
    )
    if set(frame.columns) != COLUMNS:
        raise ValueError("Hồ sơ vàng chỉ được chứa các cột mẫu ẩn danh.")
    cells = []
    for number, row in enumerate(frame.to_dict("records"), 2):
        salary = _number(row, "gross_salary", number)
        if salary <= 0:
            raise ValueError(f"Dòng {number}: gross_salary phải dương.")
        for field, allowed in (("role", ROLE_ORDER), ("level", LEVELS), ("region", REGIONS)):
            if row[field] not in allowed:
                raise ValueError(f"Dòng {number}: {field} không thuộc nhãn chuẩn.")
        years = _number(row, "experience_years", number)
        if not 0 <= years <= 60:
            raise ValueError(f"Dòng {number}: experience_years phải trong khoảng 0–60.")
        year = _number(row, "year", number)
        if not year.is_integer() or not 2023 <= year <= CURRENT_YEAR:
            raise ValueError(f"Dòng {number}: year phải là năm nguyên trong 2023–{CURRENT_YEAR}.")
        skills = [skill.strip() for skill in row["skills"].split("|") if skill.strip()]
        if any(skill not in SKILLS for skill in skills):
            raise ValueError(f"Dòng {number}: skills không thuộc từ vựng kỹ năng.")
        row.update(experience_years=years, gross_salary=salary, year=int(year))
        profile = {**row, "skills": skills}
        prediction = advise(profile, model_name)["salary_range"]["median"]
        error = abs(prediction - salary) / salary
        cells.append(
            {
                "row": number,
                **row,
                "prediction": prediction,
                "relative_error": error,
                "passed": error <= 0.2,
            }
        )
    rate = sum(row["passed"] for row in cells) / len(cells) if cells else None
    return {
        "status": "chưa có dữ liệu" if rate is None else "đạt" if rate >= 0.7 else "không đạt",
        "passed": rate >= 0.7 if rate is not None else None,
        "total": len(cells),
        "scored": len(cells),
        "pass_rate": rate,
        "tolerance": 0.2,
        "required_rate": 0.7,
        "cells": cells,
    }
