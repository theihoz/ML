"""Hồ sơ ít dữ liệu chỉ nhận khoảng lương mở rộng, không nhận con số lương đơn lẻ (#89)."""

import pytest

from career_market.model.advisor import advise, predict_profile


def _profile(role, years, skills=(), region="Hà Nội"):
    return {"role": role, "region": region, "experience_years": years, "skills": list(skills)}


def test_tech_lead_profile_gets_only_a_band_with_a_reason():
    result = predict_profile(_profile("Tech Lead / Architect", 6, ["Java"]))
    assert result["salary"] is None
    assert result["supported"] is False
    assert result["low"] < result["high"]
    assert result["support_reasons"]


def test_lead_level_profile_gets_only_a_band():
    result = predict_profile({**_profile("Backend Developer", 6), "level": "Lead"})
    assert result["salary"] is None
    assert any("Lead" in reason for reason in result["support_reasons"])


def test_cohort_with_few_training_postings_gets_only_a_band():
    result = predict_profile(_profile("UI/UX Designer", 3))
    assert result["salary"] is None
    assert any("tin train" in reason for reason in result["support_reasons"])


def test_well_supported_backend_junior_gets_a_number_and_band():
    result = predict_profile(_profile("Backend Developer", 2, ["Java"]))
    assert result["supported"] is True
    assert result["support_reasons"] == []
    assert result["low"] < result["salary"] < result["high"]


def test_result_says_whether_the_serving_model_meets_the_standard():
    result = predict_profile(_profile("Backend Developer", 2))
    assert result["production_ready"] in (True, False)


@pytest.mark.parametrize("role", ["Tech Lead / Architect", "UI/UX Designer"])
def test_adding_a_skill_never_lowers_a_low_support_band(role):
    base = predict_profile(_profile(role, 6))
    for skill in ["Java", "Python", "AWS", "Docker", "Kubernetes"]:
        more = predict_profile(_profile(role, 6, [skill]))
        assert more["low"] >= base["low"] - 1e-6
        assert more["high"] >= base["high"] - 1e-6


def test_adding_experience_never_lowers_a_low_support_band():
    bands = [predict_profile(_profile("Tech Lead / Architect", years)) for years in (5, 6, 8, 10)]
    for before, after in zip(bands, bands[1:]):
        assert after["low"] >= before["low"] - 1e-6
        assert after["high"] >= before["high"] - 1e-6


def test_advice_for_a_low_support_profile_hides_the_number_but_keeps_guidance():
    result = advise(_profile("Tech Lead / Architect", 6, ["Java"]))
    assert result["salary"] is None
    assert result["supported"] is False
    assert result["low"] < result["high"]
    assert result["recommendations"]
    assert all(step["salary"] is None for step in result["experience_path"])
    assert all(step["low"] < step["high"] for step in result["experience_path"])


def test_advice_for_a_supported_profile_keeps_its_number():
    result = advise(_profile("Backend Developer", 2, ["Java"]))
    assert result["supported"] is True
    assert result["low"] < result["salary"] < result["high"]


def test_advisor_page_hides_the_number_for_a_low_support_profile():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=60).run()
    app.selectbox[0].set_value("Tech Lead / Architect")
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].label == "Khoảng lương (triệu đồng / tháng)"
    assert "–" in app.metric[0].value
    assert any("Ít dữ liệu" in warning.value for warning in app.warning)


def test_low_support_profile_gets_a_plain_language_message_and_posting_count():
    result = predict_profile(_profile("Tech Lead / Architect", 6))
    assert result["cohort_rows"] == 0
    message = result["support_message"]
    assert "Tech Lead / Architect" in message and "0 tin" in message
    assert "tin train" not in message and "production" not in message


def test_supported_profile_reports_how_many_postings_back_it():
    result = predict_profile(_profile("Backend Developer", 2))
    assert result["cohort_rows"] >= 20
    assert result["support_message"] == ""


def _advisor(role):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=60).run()
    app.selectbox[0].set_value(role)
    app.button[0].click().run()
    assert not app.exception
    return app


def test_advisor_leads_with_the_band_and_states_the_supporting_postings():
    app = _advisor("Backend Developer")
    assert app.metric[0].label == "Khoảng lương (triệu đồng / tháng)"
    texts = " ".join(str(item.value) for item in app.markdown)
    assert "Mức điển hình khoảng" in texts
    assert "Dựa trên" in texts and "tin cùng vai trò và cấp bậc" in texts


def test_advisor_warns_on_top_when_the_model_is_not_production_ready():
    from career_market.model.training import load_production

    app = _advisor("Backend Developer")
    shown = any("mang tính tham khảo" in str(item.value) for item in app.info)
    assert shown is (not load_production()["production_ready"])


def test_low_support_advice_hides_salary_uplift_amounts():
    app = _advisor("Tech Lead / Architect")
    table = app.dataframe[0].value
    assert "Tăng lương (triệu)" not in table.columns
    assert set(table["Lý do"]) <= {"Có thể giúp tăng lương", "Được yêu cầu nhiều"}
    assert any(expander.label == "Vì sao?" for expander in app.expander)
