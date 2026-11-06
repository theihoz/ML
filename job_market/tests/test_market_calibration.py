"""Market calibration behavior through advice and reality-check seams."""

import pytest

from career_market.model.advisor import advise
from career_market.model.reality import reality_check

PROFILE = {"role": "Backend Developer", "region": "Hà Nội", "experience_years": 2, "skills": []}


def test_market_is_primary_and_advertised_is_kept_separate():
    result = advise(PROFILE)
    assert result["salary_range"] == result["market_range"]
    assert result["market_range"] != result["advertised_range"]
    assert result["calibration"]["basis"] == "gross"
    assert result["calibration"]["approximate"] is True
    assert result["low"] < result["salary"] < result["high"]


@pytest.mark.parametrize("name", ["Ridge", "RandomForest", "GradientBoosting"])
def test_frozen_policy_meets_reference_threshold_on_all_ten_cells(name):
    result = reality_check(model_name=name)
    assert result["reference"]["total"] == 10
    assert result["reference"]["pass_rate"] >= 0.8


@pytest.mark.parametrize("name", ["Ridge", "RandomForest", "GradientBoosting"])
def test_market_skill_monotonicity_and_levels(name):
    for city in ("Hà Nội", "TP. Hồ Chí Minh"):
        salaries = []
        for level, years in [("Intern", 0), ("Fresher", 0), ("Junior", 1)]:
            profile = {**PROFILE, "region": city, "level": level, "experience_years": years}
            before = advise(profile, name)
            after = advise({**profile, "skills": ["Java", "SQL", "Docker"]}, name)
            # Trung vị luôn được tính, kể cả khi con số hiển thị bị ẩn vì ít dữ liệu (#89).
            before, after = before["salary_range"]["median"], after["salary_range"]["median"]
            assert after >= before - 1e-6
            salaries.append(before)
        assert salaries[0] < salaries[1] < salaries[2]


@pytest.mark.parametrize("filename", ["calibration.json", "salary_reference.csv"])
def test_demo_detects_missing_calibration_inputs_before_any_loader(monkeypatch, filename):
    import runpy
    from pathlib import Path

    demo = runpy.run_path(str(Path(__file__).parents[2] / "docker" / "check_demo.py"))
    is_file = Path.is_file
    monkeypatch.setattr(Path, "is_file", lambda p: False if p.name == filename else is_file(p))

    def no_loading():
        raise AssertionError("demo must guard files before loaders")

    monkeypatch.setitem(demo["check_demo"].__globals__, "load_dataset", no_loading)
    with pytest.raises(RuntimeError, match=filename):
        demo["check_demo"]()


@pytest.mark.parametrize("filename", ["metrics.json", "GradientBoosting.joblib", "reference.csv"])
def test_advice_rejects_stale_saved_calibration(monkeypatch, tmp_path, filename):
    import shutil

    from career_market.model import calibration
    from career_market.paths import artifacts_dir, data_root

    for source in artifacts_dir().iterdir():
        if source.is_file():
            shutil.copy(source, tmp_path / source.name)
    (tmp_path / "reference").mkdir()
    shutil.copy(
        data_root() / "reference" / "salary_reference.csv",
        tmp_path / "reference" / "salary_reference.csv",
    )
    target = (
        tmp_path / filename
        if filename != "reference.csv"
        else tmp_path / "reference" / "salary_reference.csv"
    )
    with target.open("ab") as stream:
        stream.write(b"\nchanged")
    monkeypatch.setattr(calibration, "artifacts_dir", lambda: tmp_path)
    monkeypatch.setattr(calibration, "data_root", lambda: tmp_path)
    with pytest.raises(RuntimeError, match="không khớp"):
        advise(PROFILE, "GradientBoosting")


def test_reality_predictions_use_current_year_advice_transform(monkeypatch):
    import pandas as pd

    from career_market.model import reality

    # A public-seam fixture: no source outcomes substituted for model predictions.
    profiles = [
        {**PROFILE, "level": "Junior", "year": 2021, "split": "train", "skills": ""},
        {**PROFILE, "level": "Senior", "year": 2022, "split": "train", "skills": "Java"},
        {**PROFILE, "level": "Middle", "year": 2023, "split": "train", "skills": "SQL"},
    ]
    expected = sorted(
        advise({**p, "skills": p["skills"].split("|") if p["skills"] else []})["salary"]
        for p in profiles
    )[1]
    monkeypatch.setattr(reality, "load_dataset", lambda: pd.DataFrame(profiles))
    result = reality_check()
    cell = next(c for c in result["reference"]["cells"] if c["role"] == "Backend Developer")
    assert cell["prediction"] == pytest.approx(expected)
    assert result["reference"]["total"] == 10


def test_advice_explains_intern_proxy_and_missing_role_anchor():
    intern = advise({**PROFILE, "level": "Intern", "experience_years": 0})
    assert intern["calibration"]["scope"] == "fresher_proxy"
    assert intern["calibration"]["warnings"]
    rare = advise({**PROFILE, "role": "Quản trị CSDL (DBA)", "region": "Remote"})
    assert rare["calibration"]["role_factor"] == 1
    assert rare["calibration"]["scope"] == "level"
    assert len(rare["calibration"]["warnings"]) >= 2
