"""Cổng thay model: huấn luyện lại không được làm chất lượng trên production tụt im lặng."""

import json
from datetime import datetime, timezone

from career_market.model.versions import retrain_version
from career_market.paths import current_version


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


def _metrics(version):
    return {"version": version, "dataset_rows": 10, "split": {"train": 7}, "selected": "M"}


def _retrain(tmp_path, train, validate, rescore=None):
    """Huấn luyện thành phiên bản mới trong tmp_path; cổng quyết định có đổi CURRENT không."""
    return retrain_version(
        train=train,
        validate=validate,
        rescore=rescore,
        root=tmp_path,
        now=datetime(2026, 11, 7, tzinfo=timezone.utc),
    )


def _served(tmp_path):
    return tmp_path / current_version(tmp_path)


def _fake_pipeline(production, version):
    def train(output):
        output.mkdir(parents=True, exist_ok=True)
        (output / "metrics.json").write_text(json.dumps(_metrics(version)))
        (output / "Model.joblib").write_text(version)

    def validate(directory):
        (directory / "validation.json").write_text(json.dumps({"production": production}))

    return train, validate


def _serving(tmp_path, production, version="old"):
    serving = tmp_path / "salary-v2"
    serving.mkdir()
    (serving / "metrics.json").write_text(json.dumps(_metrics(version)))
    (serving / "Model.joblib").write_text(version)
    (serving / "validation.json").write_text(json.dumps({"production": production}))
    return serving


def _version(directory):
    return json.loads((directory / "metrics.json").read_text())["version"]


def test_failing_candidate_does_not_replace_a_model_that_meets_the_standard(tmp_path):
    _serving(tmp_path, _production(12, 70, 80, groups_passed=5, ready=True))
    train, validate = _fake_pipeline(_production(17, 58, 78), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is False
    assert _version(_served(tmp_path)) == "old"
    assert _version(tmp_path / result["version"]) == "new"  # phiên bản trượt vẫn được giữ
    assert "không đạt" in result["reason"]


def test_candidate_meeting_the_standard_replaces_the_serving_model(tmp_path):
    _serving(tmp_path, _production(17, 58, 78))
    train, validate = _fake_pipeline(_production(12, 70, 80, ready=True), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is True
    assert _version(_served(tmp_path)) == "new"
    served = _served(tmp_path)
    assert (served / "Model.joblib").read_text() == "new"
    assert json.loads((served / "validation.json").read_text())["production"]["production_ready"]


def test_better_candidate_replaces_a_serving_model_that_is_not_yet_ready(tmp_path):
    _serving(tmp_path, _production(17, 58, 76, groups_passed=2))
    train, validate = _fake_pipeline(_production(16, 61, 79, groups_passed=4), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is True
    assert _version(_served(tmp_path)) == "new"


def test_candidate_worse_on_one_overall_metric_is_kept_out(tmp_path):
    _serving(tmp_path, _production(17, 58, 79, groups_passed=2))
    train, validate = _fake_pipeline(_production(16, 61, 72, groups_passed=4), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is False
    assert _version(_served(tmp_path)) == "old"
    assert "coverage_pct" in result["reason"]


def test_candidate_with_equal_scopes_but_better_overall_metrics_is_promoted(tmp_path):
    # Chủ dự án chốt ngày 06/11/2026 (#81): bằng số phạm vi mà tốt hơn hẳn ở ít nhất một chỉ
    # số chung (và không tệ hơn chỉ số nào) thì vẫn thay.
    _serving(tmp_path, _production(17, 58, 78, groups_passed=3))
    train, validate = _fake_pipeline(_production(16, 60, 79, groups_passed=3), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is True


def test_identical_retrain_does_not_replace_the_serving_model(tmp_path):
    _serving(tmp_path, _production(17, 58, 78, groups_passed=3))
    train, validate = _fake_pipeline(_production(17, 58, 78, groups_passed=3), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is False
    assert _version(_served(tmp_path)) == "old"


def test_candidate_passing_fewer_scopes_is_kept_out(tmp_path):
    _serving(tmp_path, _production(17, 58, 78, groups_passed=4))
    train, validate = _fake_pipeline(_production(16, 60, 79, groups_passed=3), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is False


def test_first_training_without_a_serving_model_is_promoted(tmp_path):
    train, validate = _fake_pipeline(_production(17, 58, 78), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is True
    assert _version(_served(tmp_path)) == "new"


def test_serving_model_is_rescored_on_the_candidates_data_before_comparing(tmp_path):
    # Bản chấm cũ của model đang phục vụ (trên dữ liệu cũ) trông tốt hơn ứng viên, nhưng chấm
    # lại trên cùng tập test mới thì nó tệ hơn: cổng phải dùng bản chấm lại (#81).
    serving = _serving(tmp_path, _production(15, 66, 80, groups_passed=5))
    train, validate = _fake_pipeline(_production(16, 61, 79, groups_passed=4), "new")
    rescored = []

    def rescore(directory, output):
        rescored.append((directory, output))
        output.write_text(json.dumps({"production": _production(18, 55, 74, groups_passed=2)}))

    result = _retrain(tmp_path, train, validate, rescore)
    assert rescored and rescored[0][0] == serving
    assert result["promoted"] is True
    assert result["serving_rescored"] is True


def test_coverage_inside_the_standard_band_does_not_count_as_worse(tmp_path):
    # 83% xa 80% hơn 80.2% nhưng vẫn trong khoảng chuẩn 75–85%: không bị tính là tệ hơn.
    _serving(tmp_path, _production(18.0, 53.8, 80.2, groups_passed=2))
    train, validate = _fake_pipeline(_production(16.4, 56.2, 83.0, groups_passed=3), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is True


def test_coverage_leaving_the_standard_band_counts_as_worse(tmp_path):
    _serving(tmp_path, _production(18.0, 53.8, 84.0, groups_passed=2))
    train, validate = _fake_pipeline(_production(16.4, 56.2, 86.0, groups_passed=3), "new")
    result = _retrain(tmp_path, train, validate)
    assert result["promoted"] is False
    assert "coverage_pct" in result["reason"]
