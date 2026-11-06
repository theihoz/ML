"""Hồ sơ vàng are scored only through the saved-model reality-check seam."""

import pandas as pd
import pytest

from career_market.model.advisor import advise
from career_market.model.reality import reality_check

PROFILE = {
    "role": "Backend Developer",
    "level": "Junior",
    "region": "Hà Nội",
    "experience_years": 2,
    "skills": "Java|SQL",
    "gross_salary": 22,
    "year": 2026,
}


def write_profiles(tmp_path, rows):
    path = tmp_path / "golden.csv"
    pd.DataFrame(rows, columns=PROFILE).to_csv(path, index=False)
    return path


def test_shipped_golden_template_is_unscored():
    golden = reality_check()["golden"]
    assert golden["status"] == "chưa có dữ liệu"
    assert golden["passed"] is None
    assert golden["total"] == golden["scored"] == 0
    assert golden["pass_rate"] is None
    assert golden["cells"] == []
    assert golden["tolerance"] == 0.2
    assert golden["required_rate"] == 0.7


@pytest.mark.parametrize(
    ("offsets", "rate", "passed"),
    [([1.0, 1.01, 1.02, None], 0.75, True), ([1.0, 1.01, None, None], 0.5, False)],
)
def test_literal_golden_salaries_control_acceptance(tmp_path, offsets, rate, passed):
    prediction = advise({**PROFILE, "skills": ["Java", "SQL"]})["salary_range"]["median"]
    # Lương gần dự đoán thì đạt; lương 1.000 triệu được chỉ định độc lập nên phải trượt.
    salaries = [prediction * k if k else 1000 for k in offsets]
    path = write_profiles(tmp_path, [{**PROFILE, "gross_salary": pay} for pay in salaries])
    golden = reality_check(golden_path=path)["golden"]
    assert golden["total"] == golden["scored"] == 4
    assert golden["pass_rate"] == rate
    assert golden["passed"] is passed
    assert golden["status"] == ("đạt" if passed else "không đạt")
    # Compare the scored pay with the public user-facing prediction.
    assert golden["cells"][0]["prediction"] == pytest.approx(prediction)
    assert golden["cells"][0]["relative_error"] == pytest.approx(0, abs=1e-6)
    assert golden["cells"][-1]["relative_error"] == pytest.approx(1 - prediction / 1000)
    assert golden["cells"][-1]["passed"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("gross_salary", 0),
        ("gross_salary", -1),
        ("gross_salary", "NaN"),
        ("gross_salary", "inf"),
        ("gross_salary", "unknown"),
        ("role", "Unknown"),
        ("level", "Unknown"),
        ("region", "Unknown"),
        ("skills", "Java|Unknown"),
        ("experience_years", -1),
        ("experience_years", "NaN"),
        ("experience_years", 61),
        ("year", 2022),
        ("year", 2027),
        ("year", 2025.5),
        ("year", "NaN"),
    ],
)
def test_invalid_golden_profile_is_rejected_with_field_and_row(tmp_path, field, value):
    path = write_profiles(tmp_path, [{**PROFILE, field: value}])
    with pytest.raises(ValueError, match=f"Dòng 2: {field}"):
        reality_check(golden_path=path)


def test_golden_rejects_personal_or_missing_columns(tmp_path):
    path = tmp_path / "golden.csv"
    for columns in ([*PROFILE, "name"], [key for key in PROFILE if key != "gross_salary"]):
        pd.DataFrame(columns=columns).to_csv(path, index=False)
        with pytest.raises(ValueError, match="cột mẫu ẩn danh"):
            reality_check(golden_path=path)


def test_blank_skills_are_valid_and_old_year_is_retained(tmp_path):
    path = write_profiles(tmp_path, [{**PROFILE, "skills": "", "year": 2023}])
    golden = reality_check(golden_path=path)["golden"]
    assert golden["scored"] == 1
    assert golden["cells"][0]["skills"] == ""
    assert golden["cells"][0]["year"] == 2023
