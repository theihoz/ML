"""Ranges and shareable profiles, through the agreed advice and UI seams."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from career_market.data.dataset import load_dataset
from career_market.model.advisor import advise
from career_market.model.estimators import feature_frame
from career_market.model.training import load_model

APP = Path(__file__).parents[1] / "app.py"
PROFILE = {
    "role": "Backend Developer",
    "region": "Hà Nội",
    "experience_years": 1,
    "level": "Senior",
    "skills": [],
}


@pytest.mark.parametrize("model_name", ["Ridge", "RandomForest", "GradientBoosting"])
def test_advice_quartiles_use_the_requested_models_validation_distribution(model_name):
    valid = load_dataset().query("split == 'valid'")
    model, _, _ = load_model(model_name)
    ratios = valid["salary"].to_numpy() / model.predict(feature_frame(valid))
    # Independent empirical definition: each model uses its own held-out distribution.
    raw = float(
        model.predict(feature_frame(pd.DataFrame([{**PROFILE, "year": 2026, "skills": ""}])))[0]
    )
    expected = raw * np.quantile(ratios, [0.25, 0.5, 0.75])
    result = advise(PROFILE, model_name)
    assert list(result["advertised_range"].values()) == pytest.approx(expected)
    assert result["low"] < result["salary"] < result["high"]
    assert result["salary"] == result["salary_range"]["median"]


@pytest.mark.parametrize("model_name", ["Ridge", "RandomForest", "GradientBoosting"])
def test_experience_path_starts_at_explicit_level_and_uses_advice_median(model_name):
    result = advise(PROFILE, model_name)
    first = result["experience_path"][0]
    assert first["level"] == "Senior"
    assert first["salary"] == pytest.approx(result["salary"])
    for step in result["experience_path"]:
        future = {**PROFILE, **step}
        assert step["salary"] == pytest.approx(advise(future, model_name)["salary"])
    for recommendation in result["recommendations"]:
        after = advise({**PROFILE, "skills": [recommendation["skill"]]}, model_name)
        assert recommendation["uplift"] == pytest.approx(after["salary"] - result["salary"])


@pytest.mark.parametrize(
    ("role", "region", "priority"),
    [
        ("Backend Developer", "Hà Nội", True),
        ("Backend Developer", "Đà Nẵng", False),
        ("Backend Developer", "Remote", False),
        ("Business Analyst", "TP. Hồ Chí Minh", True),
        ("Quản trị CSDL (DBA)", "Hà Nội", False),
    ],
)
def test_advice_warns_for_outside_priority_and_thin_training_cohorts(role, region, priority):
    result = advise({**PROFILE, "role": role, "region": region})
    flag = result["data_sufficiency"]
    assert flag["in_priority"] is priority
    frame = load_dataset()
    count = len(
        frame.query(
            "split == 'train' and role == @role and region == @region and level == 'Senior'"
        )
    )
    assert flag["train_postings"] == count
    assert flag["thin_cohort"] is (count < 20)
    assert bool(flag["warnings"]) is (not priority or count < 20)


def test_shared_profile_preserves_explicit_level_model_empty_skills_and_defaults():
    app = AppTest.from_file(str(APP), default_timeout=60)
    app.query_params.update(
        role="Backend Developer",
        region="Đà Nẵng",
        years="1",
        level="Senior",
        model="Ridge",
        skills="",
    )
    app.run()
    assert not app.exception
    assert app.multiselect[0].value == []
    assert app.selectbox(key="advisor_level").value == "Senior"
    assert app.selectbox(key="advisor_model").value == "Ridge"
    result = advise({**PROFILE, "region": "Đà Nẵng"}, "Ridge")
    shown = [float(x) for x in app.metric[0].value.split(" – ")]
    interval = result["salary_range"]
    assert shown == pytest.approx([interval["p25"], interval["p75"]], abs=0.05)
    assert f"{interval['median']:.1f} triệu" in " ".join(str(m.value) for m in app.markdown)
    assert app.warning
    app.selectbox(key="advisor_level").set_value("Tự suy từ kinh nghiệm")
    app.number_input[0].set_value(0.0)
    app.button[0].click().run()
    assert not app.exception
    assert app.query_params["level"] == ""
    app.number_input[0].set_value(6.0)
    app.button[0].click().run()
    assert not app.exception
    assert app.selectbox(key="advisor_level").value == "Tự suy từ kinh nghiệm"
    assert app.number_input[0].value == 6.0
    assert app.session_state["advisor_result"]["level"] == "Senior"
    replay = AppTest.from_file(str(APP), default_timeout=60)
    replay.query_params.update(app.query_params)
    replay.run()
    assert not replay.exception
    assert (
        replay.session_state["advisor_result"]["salary_range"]
        == app.session_state["advisor_result"]["salary_range"]
    )


def test_role_position_is_shown_in_words_with_an_explanation():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button[0].click().run()
    assert not app.exception
    result = app.session_state["advisor_result"]
    position = next(m for m in app.metric if m.label == "Vị trí so với vai trò")
    share = result["market"]["percentile"]
    assert position.value == f"Cao hơn {share:.0f}% tin"
    assert f"P{share:.0f}" in position.help and "không phải lương gross" in position.help
