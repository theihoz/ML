"""Training integration uses admitted real observations, never synthetic model data."""

from career_market import MarketService


def test_adjudication_requires_evidence_and_keeps_conflicts_out_of_training():
    result = MarketService().adjudicate_training_labels()
    assert result["accepted_entities"] == 14
    assert result["company_count"] == 11
    rows = result["rows"]
    assert all(r["salary_currency"] == "VND" and r["salary_period"] == "MONTH" for r in rows)
    assert all(r["salary_basis"] == "unknown" for r in rows)
    assert all(r["compensation_scope"] == "salary_components_unspecified" for r in rows)
    assert not {1483, 6777, 1000}.intersection(r["source_row"] for r in rows)
    assert next(r for r in rows if r["source_row"] == 850)["salary_target_vnd_month"] == 85000000
    assert all(r["experience_min"] is None for r in rows)


def test_readiness_locks_policy_and_disjoint_company_membership_before_fit():
    result = MarketService().training_readiness()
    assert result["ready"] is True
    assert result["policy_sha256"]
    assert result["labels_sha256"]
    membership = result["split"]["membership"]
    groups = {}
    for row in membership:
        groups.setdefault(row["group_id"], set()).add(row["split"])
    assert all(len(parts) == 1 for parts in groups.values())
    assert set(r["split"] for r in membership) == {"train", "validation", "test"}


def test_offline_train_cli_returns_real_model_metrics_and_saved_artifacts():
    import json
    import os
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "career_market", "train"],
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "trained"
    assert report["counts"] == {"train": 10, "validation": 2, "test": 2}
    assert set(report["metrics"]) == {"Ridge", "LinearRegression", "train_median_baseline"}
    assert all(report["metrics"][model]["test"]["n"] == 2 for model in report["metrics"])
    assert not any("company" in name or "salary" in name for name in report["feature_names"])


def test_fresh_process_reload_matches_saved_predictions_and_train_only_vocabulary():
    import json
    import os
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "career_market", "training-report"],
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["reload_check"]["consistent"] is True
    assert audit["reload_check"]["max_absolute_error_vnd"] < 0.01
    assert "role=Fullstack" not in audit["report"]["feature_names"]
    assert audit["report"]["chosen_model"] == "Ridge"


def test_skill_parser_keeps_go_inside_engineering_language_list():
    result = MarketService().extract_skills("Middle Backend Engineer (Python / Go / Java / C#)")
    assert "Go" in result["skills"]


def test_new_output_directory_cannot_bypass_exposed_test_reservation(tmp_path):
    import pytest

    from career_market import MarketError

    with pytest.raises(MarketError, match="already reserved/evaluated"):
        MarketService().train_models(output_root=tmp_path / "other-destination")
    assert not list(tmp_path.rglob("*.joblib"))


def test_incomplete_or_traversing_artifact_manifest_is_rejected(tmp_path):
    import json
    import shutil
    from pathlib import Path

    import pytest

    from career_market import MarketError

    original = Path(MarketService().audit_training_run()["artifact_directory"])
    directory = tmp_path / "copied-run"
    shutil.copytree(original, directory)
    path = directory / "report.json"
    report = json.loads(path.read_text())
    original_report = json.loads(path.read_text())
    report["artifact_sha256"] = {}
    path.write_text(json.dumps(report))
    with pytest.raises(MarketError, match="Incomplete"):
        MarketService().audit_training_run(directory)
    report["chosen_model"] = "../../other-model"
    path.write_text(json.dumps(report))
    with pytest.raises(MarketError, match="Unknown chosen model"):
        MarketService().audit_training_run(directory)
    original_report["promoted"] = not original_report["promoted"]
    path.write_text(json.dumps(original_report))
    with pytest.raises(MarketError, match="not an approved local training run"):
        MarketService().audit_training_run(directory)


def test_training_report_page_loads_saved_run_without_fit():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "pages/12_Huan_luyen.py").run(
        timeout=30
    )
    assert not page.exception
    assert any(metric.value == "Ridge" for metric in page.metric)
    assert page.warning
