"""Phiên bản model và quay lại bản cũ (#108): đổi con trỏ CURRENT là đổi model phục vụ."""

import json
from datetime import datetime, timezone

import pytest

from career_market import paths
from career_market.model import versions


def _production(ready, median=20.0):
    metric = {"point": median, "ci95": [median, median], "threshold": 0, "pass": ready}
    return {
        "production_ready": ready,
        "overall": {
            "status": "pass" if ready else "fail",
            "metrics": {
                "median_error_pct": metric,
                "within_20_pct": {**metric, "point": 50.0},
                "coverage_pct": {**metric, "point": 80.0},
            },
        },
        "role": [],
        "level": [],
        "failing": {"role": [], "level": []},
    }


def _write_version(directory, ready, median=20.0):
    directory.mkdir(parents=True, exist_ok=True)
    metrics = {"dataset_rows": 10, "split": {"train": 7}, "selected": "GradientBoosting"}
    (directory / "metrics.json").write_text(json.dumps(metrics))
    (directory / "validation.json").write_text(
        json.dumps({"production": _production(ready, median)})
    )


@pytest.fixture
def root(tmp_path, monkeypatch):
    _write_version(tmp_path / "salary-v2", ready=False, median=20.0)
    monkeypatch.setattr(paths, "artifacts_root", lambda: tmp_path)
    monkeypatch.setattr(versions, "artifacts_root", lambda: tmp_path)
    return tmp_path


def _retrain(root, ready, median, second):
    return versions.retrain_version(
        train=lambda directory: _write_version(directory, ready, median),
        validate=lambda directory: None,
        root=root,
        now=datetime(2026, 11, 6, 10, 0, second, tzinfo=timezone.utc),
    )


def test_first_version_is_served_without_a_pointer(root):
    assert paths.current_version(root) == "salary-v2"
    assert paths.artifacts_dir() == root / "salary-v2"


def test_passing_candidate_moves_current_and_failing_one_is_kept(root):
    passed = _retrain(root, ready=True, median=10.0, second=1)
    assert passed["promoted"] is True
    assert paths.artifacts_dir() == root / passed["version"]
    failed = _retrain(root, ready=False, median=40.0, second=2)
    assert failed["promoted"] is False
    assert paths.current_version(root) == passed["version"]
    assert (root / failed["version"] / "manifest.json").exists()  # giữ lại để phân tích
    listed = {row["version"]: row for row in versions.list_versions(root)}
    assert listed[passed["version"]]["current"] is True
    assert listed[failed["version"]]["promoted"] is False
    assert listed[passed["version"]]["production_ready"] is True


def test_rollback_returns_to_the_previous_served_version(root):
    first = _retrain(root, ready=True, median=10.0, second=1)
    second = _retrain(root, ready=True, median=9.0, second=2)
    assert paths.current_version(root) == second["version"]
    assert versions.rollback(root)["current"] == first["version"]
    assert paths.artifacts_dir() == root / first["version"]
    assert versions.rollback(root)["current"] == "salary-v2"
    with pytest.raises(ValueError):
        versions.rollback(root)


def test_shipped_first_version_has_a_manifest_matching_its_metrics():
    manifest = versions.current_manifest()
    metrics = json.loads((paths.artifacts_dir() / "metrics.json").read_text())
    assert manifest["version"] == paths.current_version()
    assert manifest["train_rows"] == metrics["split"]["train"]


@pytest.mark.parametrize("page", [None, "pages/dataset.py"])
def test_advisor_and_dataset_pages_show_the_freshness_line(page):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=60).run()
    if page:
        app.switch_page(page).run(timeout=60)
    assert not app.exception
    manifest = versions.current_manifest()
    line = next(c.value for c in app.caption if c.value.startswith("Phiên bản"))
    assert manifest["version"] in line
    assert f"{manifest['train_rows']:,} tin train" in line
    assert (manifest["last_import"] or manifest["created_at"])[:10] in line
    expected = "đạt chuẩn production" if manifest["production_ready"] else "bản thử nghiệm"
    assert expected in line


def test_freshness_line_marks_unready_models_as_trial():
    manifest = {"version": "v", "created_at": "2026-11-06T00:00:00", "train_rows": 1234}
    assert "bản thử nghiệm" in versions.freshness_line({**manifest, "production_ready": False})
    assert "đạt chuẩn" in versions.freshness_line({**manifest, "production_ready": True})


def test_use_latest_serves_the_newest_version_even_if_it_failed_the_gate(root):
    first = _retrain(root, ready=True, median=10.0, second=1)
    failed = _retrain(root, ready=False, median=40.0, second=2)
    assert paths.current_version(root) == first["version"]  # cổng giữ bản cũ
    loaded = versions.use_version("latest", root)
    assert loaded["current"] == failed["version"] == paths.current_version(root)
    assert loaded["production_ready"] is False
    assert versions.rollback(root)["current"] == first["version"]  # vẫn quay lại được


def test_use_named_version_and_reject_unknown(root):
    assert versions.use_version("salary-v2", root)["current"] == "salary-v2"
    with pytest.raises(ValueError, match="Không có phiên bản"):
        versions.use_version("khong-co", root)


def test_score_rows_cover_every_model_on_three_splits():
    from career_market.model.training import load_report, score_rows

    report = load_report()
    rows = score_rows(report)
    assert len(rows) == 3 * len(report["models"])
    selected = [r for r in rows if r["selected"] and r["part"] == "test"]
    assert selected[0]["MAE"] == report["models"][report["selected"]]["test"]["MAE"]
