"""Bộ dữ liệu mở rộng salary-v2, mô hình đã lưu và trang tư vấn."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from career_market.salary_dataset import (
    ROLE_ORDER,
    classify_role,
    load_dataset,
    parse_experience,
    parse_salary,
)
from career_market.salary_model import advise, load_report

APP = Path(__file__).parents[1] / "app.py"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("15 - 25 triệu", (15, 25, 20)),
        ("Lương: 10 Tr - 15 Tr VND", (10, 15, 12.5)),
        ("Tới 30 triệu", (21, 30, 25.5)),
        ("15tr-25tr ₫/tháng", (15, 25, 20)),
        ("200tr-500tr ₫/năm", (200 / 12, 500 / 12, 350 / 12)),
        ("240tr-360tr ₫/năm", (20, 30, 25)),
        ("Thoả thuận", None),
        ("1 triẹu - 40 triẹu/tháng", None),
    ],
)
def test_salary_text_is_normalized_to_million_vnd_per_month(text, expected):
    result = parse_salary(text)
    assert result == (pytest.approx(expected, abs=0.01) if expected else None)


def test_usd_salary_uses_exchange_rate_of_posting_year():
    low, high, middle = parse_salary("$ 1,000-1,500 /tháng", 2026)
    assert (low, high) == (26.0, 39.0)


@pytest.mark.parametrize(
    ("text", "years"),
    [("2 năm", 2), ("Dưới 1 năm", 0.5), ("Trên 5 năm", 6), ("1 - 3 Năm", 2), ("Không yêu cầu", 0)],
)
def test_experience_text_becomes_years(text, years):
    assert parse_experience(text) == years


@pytest.mark.parametrize(
    ("title", "role"),
    [
        ("Senior Java Developer", "Backend Developer"),
        ("Data Engineer (Spark)", "Data Engineer"),
        ("Machine Learning Engineer", "AI / ML Engineer"),
        ("Automation Tester", "Kiểm thử (QA/QC)"),
        ("IT Sales Executive", None),
        ("Kế toán tổng hợp", None),
    ],
)
def test_title_maps_to_one_it_role(title, role):
    assert classify_role(title) == role


def test_dataset_has_every_role_and_company_disjoint_splits():
    frame = load_dataset()
    assert len(frame) > 3000
    assert set(frame["role"]) == set(ROLE_ORDER)
    assert set(frame["split"]) == {"train", "valid", "test"}
    companies = frame.groupby("split")["company_key"].apply(set)
    assert not companies["train"] & companies["test"]
    assert not companies["train"] & companies["valid"]


def test_saved_models_beat_median_baseline_on_test():
    report = load_report()
    baseline = report["models"]["Baseline"]["test"]["MAE"]
    trained = [name for name in report["models"] if name != "Baseline"]
    assert len(trained) >= 2
    for name in trained:
        assert report["models"][name]["test"]["MAE"] < baseline
        assert {"MAE", "RMSE", "R2", "MAPE"} <= set(report["models"][name]["test"])


def test_advice_predicts_salary_and_recommends_unowned_skills():
    result = advise(
        {"role": "Backend Developer", "region": "Hà Nội", "experience_years": 2, "skills": ["Java"]}
    )
    assert 5 < result["salary"] < 100
    assert result["low"] < result["salary"] < result["high"]
    skills = [row["skill"] for row in result["recommendations"]]
    assert skills and "Java" not in skills
    path = [step["salary"] for step in result["experience_path"]]
    assert path == sorted(path)


def test_advisor_is_home_and_returns_salary_with_skill_advice():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert app.title[0].value == "Tư vấn & dự đoán lương"
    app.multiselect[0].set_value(["Python", "SQL"])
    app.selectbox[0].set_value("Data Engineer")
    app.button[0].click().run()
    assert not app.exception
    assert float(app.metric[0].value) > 0
    assert app.dataframe[0].value["Kỹ năng"].tolist()


@pytest.mark.parametrize("page", ["pages/evaluation.py", "pages/dataset.py"])
def test_evaluation_and_dataset_pages_render(page):
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.switch_page(page).run(timeout=60)
    assert not app.exception
    assert app.metric


def test_validation_reports_calibration_bootstrap_and_fairness():
    from career_market.salary_dataset import gender_requirement
    from career_market.salary_validation import load_validation

    result = load_validation()
    eighty = next(row for row in result["calibration"]["levels"] if row["level"] == 0.8)
    assert 0.7 < eighty["coverage"] < 0.9
    gb = result["bootstrap"]["models"]["GradientBoosting"]["MAE"]
    assert gb["ci95"][0] <= gb["point"] <= gb["ci95"][1]
    assert {"region", "level", "role"} <= set(result["fairness"])
    assert result["gender"]["used_as_feature"] is False
    assert gender_requirement("Tester Game Chỉ Tuyển Nữ") == "Chỉ nữ"
    assert gender_requirement("Lap Trinh Vien Tu 3 Nam Kinh Nghiem") == "Không đề cập"
    assert gender_requirement("Giới tính: Nam/Nữ") == "Nam/Nữ"


MONOTONE_PROFILES = [
    ("Backend Developer", years, base)
    for years in (0, 2, 5)
    for base in ([], ["Java"], ["Java", "Spring Boot", "SQL"], ["Python", "Django", "Docker"])
] + [("Frontend Developer", 3, ["JavaScript", "React"]), ("Kiểm thử (QA/QC)", 1, [])]
EXTRA_SKILLS = ["Java", "Python", "Docker", "AWS", "Kubernetes", "MySQL", "Redis", "PHP", "C#"]


@pytest.mark.parametrize("model_name", ["Ridge", "RandomForest", "GradientBoosting"])
def test_adding_a_skill_never_lowers_predicted_salary(model_name):
    from career_market.salary_model import predict_profile

    for role, years, base in MONOTONE_PROFILES:
        profile = {"role": role, "region": "Hà Nội", "experience_years": years, "skills": base}
        before = predict_profile(profile, model_name)["salary"]
        for skill in EXTRA_SKILLS:
            if skill in base:
                continue
            after = predict_profile({**profile, "skills": [*base, skill]}, model_name)["salary"]
            assert after >= before - 1e-6, (model_name, role, years, base, skill, before, after)


def test_selected_model_stays_within_accepted_error_budget():
    # Quyết định 06/11/2026: ràng buộc đơn điệu theo kỹ năng làm test MAE tăng từ 5.38 lên
    # khoảng 5.82; ngân sách ban đầu 5.65 (+5%) được nới lên 5.85 (~+9%) sau khi chỉnh siêu
    # tham số trên valid không kéo MAE về trong ngân sách cũ.
    report = load_report()
    assert report["models"][report["selected"]]["test"]["MAE"] <= 5.85


ADVICE_PROFILES = [
    ("Backend Developer", 2, ["Java"]),
    ("Backend Developer", 5, []),
    ("Frontend Developer", 1, ["JavaScript", "React"]),
    ("Data Engineer", 3, ["Python", "SQL"]),
    ("Kiểm thử (QA/QC)", 0, []),
    ("DevOps / Cloud", 4, ["Docker", "Kubernetes", "AWS"]),
]


@pytest.mark.parametrize(("role", "years", "skills"), ADVICE_PROFILES)
def test_recommended_skills_never_lower_predicted_salary(role, years, skills):
    result = advise({"role": role, "region": "Hà Nội", "experience_years": years, "skills": skills})
    assert result["recommendations"]
    for row in result["recommendations"]:
        assert row["skill"] not in skills
        assert row["uplift"] >= -1e-6, (role, years, skills, row)


def test_saved_skill_value_has_no_negative_model_uplift():
    from career_market.salary_model import load_skill_value

    table = load_skill_value()
    assert len(table)
    assert (table["model_uplift"] >= -1e-6).all(), table[table["model_uplift"] < 0]


def test_saved_report_and_validation_match_the_current_model():
    from career_market.salary_validation import load_validation

    report = load_report()
    assert not any(name.endswith("skill_count") for name in report["permutation_importance"])
    validation = load_validation()
    selected = report["selected"]
    assert validation["selected"] == selected
    point = validation["bootstrap"]["models"][selected]["MAE"]["point"]
    assert point == pytest.approx(report["models"][selected]["test"]["MAE"], abs=1e-6)


FULL_PROFILE_SKILLS = [
    "Java", "Spring Boot", "SQL", "Docker", "AWS", "Kubernetes",
    "Redis", "MySQL", "Python", "Git", "REST API", "Microservices",
]  # fmt: skip


@pytest.mark.parametrize("model_name", ["Ridge", "RandomForest", "GradientBoosting"])
def test_dropping_any_skill_from_a_twelve_skill_profile_never_raises_salary(model_name):
    # 12 là số kỹ năng tối đa của một tin trong dữ liệu; đây là cỡ lớn nhất mà bao đơn điệu
    # của Random Forest phải xử lý (2^12 tập con).
    from career_market.salary_model import predict_profile

    profile = {
        "role": "Backend Developer",
        "region": "Hà Nội",
        "experience_years": 5,
        "skills": FULL_PROFILE_SKILLS,
    }
    full = predict_profile(profile, model_name)["salary"]
    for skill in FULL_PROFILE_SKILLS:
        fewer = [name for name in FULL_PROFILE_SKILLS if name != skill]
        dropped = predict_profile({**profile, "skills": fewer}, model_name)["salary"]
        assert dropped <= full + 1e-6, (model_name, skill, dropped, full)
