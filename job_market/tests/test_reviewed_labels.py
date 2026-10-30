"""Reviewed real labels supplement only the matched postings, never all sources."""

import csv
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from career_market import MarketError, MarketService


def test_prepare_imports_two_reviewed_income_labels_but_keeps_training_blocked():
    service = MarketService()
    report = service.prepare()
    targets = {row["job_id"]: row for row in report["targets"]}
    assert {key: row["salary_target_vnd_month"] for key, row in targets.items()} == {
        "35BB58E5": 27_500_000,
        "35BB58DC": 37_500_000,
    }
    assert report["summary"]["salary_targets"] == 2
    assert report["ml_state"] == "blocked_pending_salary_gate"
    assert all(row["salary_basis"] == "unknown" for row in targets.values())
    assert all(row["compensation_scope"] == "advertised_monthly_income" for row in targets.values())
    assert all(row["salary_label_evidence"] for row in targets.values())
    assert all(row["raw"]["salary"] == row["salary_raw"] for row in targets.values())
    assert service.salary_report()["target_n"] == 0  # Raw salary-column evidence remains distinct.
    exported = service.snapshot()["files"]["salary_targets.csv"]
    assert len(list(csv.DictReader(io.StringIO(exported.decode())))) == 2


def test_cli_prepare_accepts_review_directory_and_exports_lineage(tmp_path):
    project = Path(__file__).parents[1]
    ledger = project / "datasets/labels/2026-10-29"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "career_market",
            "prepare",
            "--review-dir",
            str(ledger),
            "--output",
            str(tmp_path / "snapshot"),
        ],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project / "src")},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["reviewed_labels"]["imported_postings"] == 2
    assert manifest["ml_state"] == "blocked_pending_salary_gate"
    table = list(csv.DictReader((tmp_path / "snapshot/salary_targets.csv").open()))
    assert {row["salary_label_review_id"] for row in table} == {
        "jobs-2023:35BB58E5",
        "jobs-2023:35BB58DC",
    }


@pytest.mark.parametrize(
    "filename", ["accepted_labels.csv", "candidate_review.json", "manifest.json"]
)
def test_modified_review_files_are_rejected_without_changing_raw(filename, tmp_path):
    service = MarketService()
    original = service.raw_dir.parent / "labels/2026-10-29"
    copied = tmp_path / "review"
    shutil.copytree(original, copied)
    target = copied / filename
    target.write_bytes(target.read_bytes() + b" ")
    before = {path.name: path.read_bytes() for path in service.raw_dir.glob("*.csv")}
    with pytest.raises(MarketError, match="SHA-256"):
        service.prepare(review_dir=copied)
    assert {path.name: path.read_bytes() for path in service.raw_dir.glob("*.csv")} == before


def test_unselected_source_does_not_receive_reviewed_monthly_labels():
    report = MarketService().prepare(["jobs-2026"])
    assert report["targets"] == []
    assert report["reviewed_labels"]["imported_postings"] == 0
    assert all(row["salary_period"] is None for row in report["rows"])
