"""Chuẩn production: chấm trung vị sai số, tỉ lệ sai ≤ 20% và độ phủ khoảng p10–p90."""

import numpy as np
import pandas as pd
import pytest

from career_market.model.production import THRESHOLDS, assess

BAND = (0.9, 1.1)


def _postings(ratios, role="Backend Developer", level="Junior", start=0):
    """Tin dựng sẵn: lương thật / lương dự đoán = ratio; hai tin một công ty."""
    ratios = np.asarray(ratios, dtype=float)
    salary = np.full(len(ratios), 30.0)
    index = np.arange(start, start + len(ratios))
    return pd.DataFrame(
        {
            "salary": salary,
            "predicted": salary / ratios,
            "role": role,
            "level": level,
            "company_key": [f"c{i // 2}" for i in index],
        }
    )


def _good(n, **kwargs):
    """80% sai rất ít (nằm trong khoảng), 10% mỗi phía nằm ngoài khoảng nhưng sai < 20%."""
    rng = np.random.default_rng(0)
    inner = rng.uniform(0.95, 1.05, int(n * 0.8))
    outer = np.r_[np.full(n // 10, 0.85), np.full(n - len(inner) - n // 10, 1.15)]
    ratios = np.r_[inner, outer]
    rng.shuffle(ratios)
    return _postings(ratios, **kwargs)


def _run(frame):
    return assess(frame, frame["predicted"].to_numpy(), BAND, rounds=200, seed=1)


def test_thresholds_live_in_one_place():
    assert THRESHOLDS["overall"]["median_error_pct"] == 15
    assert THRESHOLDS["overall"]["within_20_pct"] == 65
    assert THRESHOLDS["overall"]["coverage_pct"] == (75, 85)
    assert THRESHOLDS["group"]["median_error_pct"] == 20
    assert THRESHOLDS["group"]["within_20_pct"] == 50
    assert THRESHOLDS["group"]["coverage_pct"] == (70, 100)
    assert THRESHOLDS["min_test_rows"] == 20
    assert THRESHOLDS["min_train_rows"] == 20
    assert THRESHOLDS["long_term"] == {"median_error_pct": 10, "within_20_pct": 75}


def test_accurate_model_passes_overall():
    result = _run(_good(4000))
    overall = result["overall"]
    assert overall["status"] == "pass"
    assert overall["metrics"]["coverage_pct"]["point"] == pytest.approx(80, abs=1)
    assert result["production_ready"] is True
    assert result["failing"] == {"role": [], "level": []}


def test_inaccurate_model_fails_overall():
    frame = _postings(np.full(400, 0.6))
    result = _run(frame)
    assert result["overall"]["status"] == "fail"
    assert result["overall"]["metrics"]["median_error_pct"]["pass"] is False
    assert result["production_ready"] is False


def test_one_bad_role_fails_only_that_role():
    frame = pd.concat(
        [
            _good(4000),
            _postings(np.full(30, 0.6), role="Tech Lead / Architect", start=4000),
        ],
        ignore_index=True,
    )
    result = _run(frame)
    roles = {row["group"]: row for row in result["role"]}
    assert roles["Backend Developer"]["status"] == "pass"
    assert roles["Tech Lead / Architect"]["status"] == "fail"
    assert result["failing"]["role"] == ["Tech Lead / Architect"]
    assert result["production_ready"] is False


def test_groups_under_twenty_test_rows_are_not_scored():
    frame = pd.concat(
        [_good(4000), _postings(np.full(10, 0.6), role="Game Developer", start=4000)],
        ignore_index=True,
    )
    result = _run(frame)
    game = next(row for row in result["role"] if row["group"] == "Game Developer")
    assert game["status"] == "not_scored"
    assert game["n"] == 10
    assert "Game Developer" not in result["failing"]["role"]
    assert result["production_ready"] is True


def test_point_estimate_passing_is_not_enough_when_bootstrap_bound_fails():
    # Một nửa sai 10%, một nửa sai 18%: trung vị điểm 14% (đạt) nhưng cận trên vượt 15%.
    ratios = np.r_[np.full(30, 1 / 1.10), np.full(30, 1 / 1.18)]
    result = _run(_postings(ratios))
    median = result["overall"]["metrics"]["median_error_pct"]
    assert median["point"] <= THRESHOLDS["overall"]["median_error_pct"]
    assert median["ci95"][1] > THRESHOLDS["overall"]["median_error_pct"]
    assert median["pass"] is False


def test_levels_are_scored_like_roles():
    frame = pd.concat(
        [_good(4000), _postings(np.full(40, 0.6), level="Manager", start=4000)],
        ignore_index=True,
    )
    result = _run(frame)
    assert result["failing"]["level"] == ["Manager"]


def test_groups_are_judged_on_point_estimates_overall_on_bootstrap_bounds():
    # Nhóm 40 tin: một nửa sai 10%, một nửa sai 18% → trung vị điểm 14% ≤ 20% (đạt),
    # dù khoảng bootstrap rộng. Mức chung vẫn so cận bất lợi.
    group = _postings(
        np.r_[np.full(20, 1 / 1.10), np.full(20, 1 / 1.18)], role="Bảo mật", start=4000
    )
    result = _run(pd.concat([_good(4000), group], ignore_index=True))
    security = next(row for row in result["role"] if row["group"] == "Bảo mật")
    assert security["metrics"]["median_error_pct"]["judged_on"] == "point"
    assert security["metrics"]["median_error_pct"]["pass"] is True
    assert result["overall"]["metrics"]["median_error_pct"]["judged_on"] == "ci95"
