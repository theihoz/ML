"""Streamlit form smoke through real MarketService, without model substitutes."""

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from career_market import MarketService


def test_prediction_form_submits_valid_and_invalid_profiles_without_salary_or_advice():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=20).run()
    assert not app.exception
    app.switch_page("pages/10_Du_doan.py").run()
    assert not app.exception
    assert not app.metric
    profile = {
        "role": "Backend",
        "experience": "2–4 năm",
        "skills": "ReactJS; Python",
        "location": "ho chi minh | HN",
        "work_mode": "Remote",
    }
    for key in ("role", "experience", "skills", "location"):
        app.text_input(key=f"prediction_{key}").set_value(profile[key])
    app.selectbox(key="prediction_work_mode").select("Remote")
    app.button[0].click().run()
    assert not app.exception
    result = json.loads(app.json[0].value)
    assert result == MarketService().predict_profile(profile)
    assert result["status"] == "model_unavailable"
    assert "model_unavailable" in app.warning[0].value
    assert not app.metric
    app.text_input(key="prediction_experience").set_value("")
    app.button[0].click().run()
    assert not app.exception
    result = json.loads(app.json[0].value)
    assert result["status"] == "invalid_input"
    assert result["salary_prediction"] is None
    assert result["advice"] == []
    assert "invalid_input" in app.error[0].value
    assert not app.metric
