"""Lệnh refresh chạy cả chuỗi huấn luyện lại (#109)."""

import json
from datetime import datetime, timezone

import pandas as pd
import pytest

from career_market.data.dataset import write_dataset
from career_market.model import versions
from career_market.paths import current_version
from career_market.refresh import refresh

COLUMNS = ["source", "title", "company", "location", "salary_text"]
COLUMNS += ["experience_text", "description", "url", "posted_date"]


def _write_version(directory, ready):
    directory.mkdir(parents=True, exist_ok=True)
    metrics = {"dataset_rows": 10, "split": {"train": 7}, "selected": "GradientBoosting"}
    (directory / "metrics.json").write_text(json.dumps(metrics))
    metric = {"point": 10.0, "ci95": [10.0, 10.0], "threshold": 0, "pass": ready}
    production = {
        "production_ready": ready,
        "overall": {
            "status": "pass" if ready else "fail",
            "metrics": {k: metric for k in ("median_error_pct", "within_20_pct", "coverage_pct")},
        },
        "role": [],
        "level": [],
        "failing": {"role": [], "level": []},
    }
    (directory / "validation.json").write_text(json.dumps({"production": production}))


@pytest.fixture
def setup(tmp_path):
    root = tmp_path / "artifacts"
    _write_version(root / "salary-v2", ready=False)
    csv = tmp_path / "lo.csv"
    pd.DataFrame(
        [
            ["Lô thử", "Senior Backend Developer", "Công ty Mới A", "Hà Nội", "30 - 40 triệu"]
            + ["5 năm", "Java Spring Boot", "https://example.test/r/1", "2026-11-01"],
            ["Lô thử", "Tester", "Công ty Mới B", "Hà Nội", "Thoả thuận"]
            + ["1 năm", "Selenium", "https://example.test/r/2", "2026-11-01"],
        ],
        columns=COLUMNS,
    ).to_csv(csv, index=False)
    out = tmp_path / "processed"
    out.mkdir()

    def build():
        return write_dataset(
            batches=tmp_path / "batches",
            ledger=tmp_path / "none.csv",
            output=out / "salary_dataset_v2.csv",
            queue=out / "review_queue.csv",
        )

    def retrain(batches):
        return versions.retrain_version(
            train=lambda d: _write_version(d, ready=True),
            validate=lambda d: None,
            root=root,
            batches=batches,
            now=datetime(2026, 11, 6, 12, 0, 0, tzinfo=timezone.utc),
        )

    return {"root": root, "csv": csv, "batches": tmp_path / "batches", "build": build,
            "retrain": retrain, "out": out}  # fmt: skip


def test_refresh_imports_builds_creates_a_version_and_reports_the_gate(setup):
    lines = []
    result = refresh(
        [setup["csv"]],
        build=setup["build"],
        retrain=setup["retrain"],
        batches_dir=setup["batches"],
        root=setup["root"],
        log=lines.append,
    )
    assert result["status"] == "ok"
    assert result["new_rows"] == 2
    assert result["dataset"]["review_queue"] == 1  # tin "Thoả thuận"
    assert result["gate"]["promoted"] is True
    assert result["serving_after"] == result["gate"]["version"] != result["serving_before"]
    manifest = versions.read_manifest(setup["root"] / result["gate"]["version"])
    assert manifest["batches"] and manifest["last_import"]
    assert any(line.startswith("Cổng thay model: thay model") for line in lines)
    queue = pd.read_csv(setup["out"] / "review_queue.csv")
    assert queue["reason"].tolist() == ["lương thoả thuận"]


def test_refresh_stops_on_a_batch_without_valid_rows_and_keeps_current(setup, tmp_path):
    bad = tmp_path / "hong.csv"
    pd.DataFrame([{c: "" for c in COLUMNS}]).to_csv(bad, index=False)

    def build():
        raise AssertionError("không được dựng dữ liệu khi lô hỏng")

    result = refresh(
        [bad],
        build=build,
        retrain=setup["retrain"],
        batches_dir=setup["batches"],
        root=setup["root"],
        log=lambda line: None,
    )
    assert result["status"] == "stopped" and "không có dòng hợp lệ" in result["error"]
    assert current_version(setup["root"]) == "salary-v2"
