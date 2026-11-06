"""Cổng thay model: huấn luyện lại không được làm chất lượng trên production tụt im lặng."""

import json

from career_market.model_promotion import retrain


def _production(median, within, coverage, groups_passed=0, ready=False):
    def metric(point):
        return {"point": point, "ci95": [point, point], "threshold": 0, "pass": ready}

    return {
        "production_ready": ready,
        "overall": {
            "status": "pass" if ready else "fail",
            "metrics": {
                "median_error_pct": metric(median),
                "within_20_pct": metric(within),
                "coverage_pct": metric(coverage),
            },
        },
        "role": [{"group": f"r{i}", "status": "pass"} for i in range(groups_passed)],
        "level": [],
        "failing": {"role": [], "level": []},
    }


def _fake_pipeline(production, version):
    def train(output):
        output.mkdir(parents=True, exist_ok=True)
        (output / "metrics.json").write_text(json.dumps({"version": version}))
        (output / "Model.joblib").write_text(version)

    def validate(directory):
        (directory / "validation.json").write_text(json.dumps({"production": production}))

    return train, validate


def _serving(tmp_path, production, version="old"):
    serving = tmp_path / "salary-v2"
    serving.mkdir()
    (serving / "metrics.json").write_text(json.dumps({"version": version}))
    (serving / "Model.joblib").write_text(version)
    (serving / "validation.json").write_text(json.dumps({"production": production}))
    return serving


def _version(directory):
    return json.loads((directory / "metrics.json").read_text())["version"]


def test_failing_candidate_does_not_replace_a_model_that_meets_the_standard(tmp_path):
    serving = _serving(tmp_path, _production(12, 70, 80, groups_passed=5, ready=True))
    train, validate = _fake_pipeline(_production(17, 58, 78), "new")
    result = retrain(serving, tmp_path / "candidate", train=train, validate=validate)
    assert result["promoted"] is False
    assert _version(serving) == "old"
    assert _version(tmp_path / "candidate") == "new"
    assert "không đạt" in result["reason"]


def test_candidate_meeting_the_standard_replaces_the_serving_model(tmp_path):
    serving = _serving(tmp_path, _production(17, 58, 78))
    train, validate = _fake_pipeline(_production(12, 70, 80, ready=True), "new")
    result = retrain(serving, tmp_path / "candidate", train=train, validate=validate)
    assert result["promoted"] is True
    assert _version(serving) == "new"
    assert (serving / "Model.joblib").read_text() == "new"
    assert json.loads((serving / "validation.json").read_text())["production"]["production_ready"]


def test_better_candidate_replaces_a_serving_model_that_is_not_yet_ready(tmp_path):
    serving = _serving(tmp_path, _production(17, 58, 76, groups_passed=2))
    train, validate = _fake_pipeline(_production(16, 61, 79, groups_passed=4), "new")
    result = retrain(serving, tmp_path / "candidate", train=train, validate=validate)
    assert result["promoted"] is True
    assert _version(serving) == "new"


def test_candidate_worse_on_one_overall_metric_is_kept_out(tmp_path):
    serving = _serving(tmp_path, _production(17, 58, 79, groups_passed=2))
    train, validate = _fake_pipeline(_production(16, 61, 72, groups_passed=4), "new")
    result = retrain(serving, tmp_path / "candidate", train=train, validate=validate)
    assert result["promoted"] is False
    assert _version(serving) == "old"
    assert "coverage_pct" in result["reason"]


def test_candidate_that_passes_no_more_scopes_is_kept_out(tmp_path):
    serving = _serving(tmp_path, _production(17, 58, 78, groups_passed=3))
    train, validate = _fake_pipeline(_production(16, 60, 79, groups_passed=3), "new")
    result = retrain(serving, tmp_path / "candidate", train=train, validate=validate)
    assert result["promoted"] is False


def test_first_training_without_a_serving_model_is_promoted(tmp_path):
    train, validate = _fake_pipeline(_production(17, 58, 78), "new")
    result = retrain(tmp_path / "salary-v2", tmp_path / "candidate", train=train, validate=validate)
    assert result["promoted"] is True
    assert _version(tmp_path / "salary-v2") == "new"
