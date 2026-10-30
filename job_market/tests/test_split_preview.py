"""Synthetic data verifies allocation only; no fitting or model metrics."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from career_market import MarketService


def observation(index, company=None, **extra):
    return {
        "source_id": "fixture",
        "posting_id": str(index),
        "job_id": str(index),
        "job_url": f"https://example.org/{index}",
        "company_raw": company or f"Company {index}",
        "partition": "eda",
        "salary_target_vnd_month": 20000000,
        "salary_currency": "VND",
        "salary_period": "MONTH",
        "salary_basis": "unknown",
        "compensation_scope": "advertised_monthly_income",
        **extra,
    }


def preview(rows):
    return MarketService().preview_split(rows, basis="unknown", scope="advertised_monthly_income")


def test_three_partitions_are_reproducible_without_company_or_repost_leakage():
    rows = [observation(i) for i in range(20)]
    rows += [observation(21, "COMPANY 0"), observation(21, "Company 0")]
    rows[1]["repost_group_id"] = rows[2]["repost_group_id"] = "linked"
    result = preview(rows)
    assert result == preview(list(reversed(rows)))
    assert result["status"] == "preview_only"
    assert result["training_ready"] is False
    assert set(result["counts"]) == {"train", "validation", "test"}
    assert all(result["counts"].values())
    assert sum(result["counts"].values()) == 21
    assert result["target_ratios"] == {"train": 0.7, "validation": 0.15, "test": 0.15}
    for key in ("company_canonical", "group_id"):
        assignments = {}
        for row in result["membership"]:
            assignments.setdefault(row[key], set()).add(row["split"])
        assert all(len(splits) == 1 for splits in assignments.values())
    assert "salary_target_vnd_month" not in result["membership"][0]
    assert len(result["membership_sha256"]) == 64


def test_one_company_is_blocked_and_cohorts_are_not_combined():
    rows = [observation(1, "YODY"), observation(2, "YODY")]
    rows += [observation(3, salary_basis="net"), observation(4, salary_basis="gross")]
    result = preview(rows)
    assert result["status"] == "blocked"
    assert "insufficient_independent_labeled_groups" in result["blockers"]
    assert result["membership"] == []
    assert result["eligible_entities"] == 2
    assert result["eligible_groups"] == 1
    assert result["training_ready"] is False


def test_conflicting_duplicate_targets_are_quarantined_not_first_row_wins():
    rows = [observation(i) for i in range(4)]
    rows.append(observation(0, salary_target_vnd_month=30000000))
    result = preview(rows)
    assert "conflicting_entity_targets" in result["blockers"]
    assert result["status"] == "blocked"
    assert result["membership"] == []


def test_equal_groups_reach_target_ratios_and_skewed_groups_stay_whole():
    result = preview([observation(i) for i in range(20)])
    assert result["counts"] == {"train": 14, "validation": 3, "test": 3}
    rows = [observation(i, "Large company") for i in range(18)]
    rows += [observation(18), observation(19)]
    result = preview(rows)
    assert sorted(result["counts"].values()) == [1, 1, 18]
    assert sum(result["actual_ratios"].values()) == 1


def test_real_cli_and_page_show_current_blocker_without_model(tmp_path):
    import json
    import os
    import subprocess
    import sys

    output = tmp_path / "preview.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "career_market",
            "split-preview",
            "--basis",
            "unknown",
            "--scope",
            "advertised_monthly_income",
            "--output",
            str(output),
        ],
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(completed.stdout)
    assert result == json.loads(output.read_text())
    assert result["eligible_entities"] == 2
    assert result["eligible_groups"] == 1
    assert result["membership"] == []
    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "pages/tools/split.py").run(
        timeout=30
    )
    assert not page.exception
    assert page.error
    assert page.warning
