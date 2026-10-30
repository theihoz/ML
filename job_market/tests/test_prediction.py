"""Synthetic profiles test behavior only, never model quality."""

from career_market import MarketService


def test_single_profile_shares_csv_normalization_without_a_salary_or_advice():
    service = MarketService()
    profile = {
        "role": " backend ",
        "experience": "2–4 năm",
        "skills": "ReactJS; Python",
        "location": "ho chi minh | HN | Remote",
    }
    result = service.predict_profile(profile)
    assert result["status"] == "model_unavailable"
    assert result["reason"]
    assert result["salary_prediction"] is None
    assert result["advice"] == []
    normalized = result["profile"]
    assert normalized["role"] == "Backend"
    assert (normalized["experience_min"], normalized["experience_max"]) == (2, 4)
    assert normalized["experience_kind"] == "range"
    assert normalized["locations"] == ["HCM", "HN"]
    assert normalized["work_modes"] == ["Remote"]
    assert set(normalized["skills"]) == {"React", "Python"}
    assert normalized["raw"] == profile
    content = (
        "role,experience,skills,location\n"
        " backend ,2–4 năm,ReactJS; Python,ho chi minh | HN | Remote\n"
    ).encode()
    row = service.preview_profiles(content, {key: key for key in profile})["rows"][0]
    for key, value in normalized.items():
        assert row[key] == value


def test_single_and_csv_profiles_keep_missing_zero_bounds_and_work_mode_evidence():
    import csv
    import io

    service = MarketService()
    cases = [
        ("", None, None, "missing", "invalid_input"),
        ("0", 0, 0, "exact", "model_unavailable"),
        ("trên 3 năm", 3, None, "greater_than", "model_unavailable"),
        ("dưới 2 năm", None, 2, "less_than", "model_unavailable"),
        ("-1", None, None, "exact", "invalid_input"),
        ("61", None, None, "exact", "invalid_input"),
    ]
    for raw, low, high, kind, status in cases:
        profile = {
            "role": "Data/ML",
            "experience": raw,
            "skills": "Python",
            "location": "Hồ Chí Minh",
            "work_mode": "làm việc từ xa",
        }
        result = service.predict_profile(profile)
        assert result["status"] == status
        assert result["salary_prediction"] is None
        assert result["advice"] == []
        normalized = result["profile"]
        assert (
            normalized["experience_min"],
            normalized["experience_max"],
            normalized["experience_kind"],
        ) == (low, high, kind)
        assert normalized["locations"] == ["HCM"]
        assert normalized["work_modes"] == ["Remote"]
        content = io.StringIO()
        writer = csv.DictWriter(content, fieldnames=list(profile))
        writer.writeheader()
        writer.writerow(profile)
        row = service.preview_profiles(content.getvalue().encode(), {key: key for key in profile})[
            "rows"
        ][0]
        assert {key: row[key] for key in normalized} == normalized
    result = service.predict_profile(
        {"role": "Backend", "experience": "2", "skills": "remote sensing", "work_mode": ""}
    )
    assert result["profile"]["work_modes"] == []
    assert result["profile"]["locations"] == []


def test_invalid_profile_shapes_and_values_return_reasons_without_predictions():
    service = MarketService()
    for profile in [
        None,
        [],
        "Backend",
        {},
        {"role": None},
        {"role": ["Backend"], "experience": "2"},
        {"role": "Backend", "experience": "2", "skills": ["Python"]},
        {"role": "Backend", "experience": "2", "location": 42},
        {"role": "Backend", "experience": "2", "work_mode": "remote sensing"},
        {"role": "astronaut", "experience": "2"},
    ]:
        result = service.predict_profile(profile)
        assert result["status"] == "invalid_input"
        assert result["reason"]
        assert result["salary_prediction"] is None
        assert result["advice"] == []


def test_cli_predict_returns_service_status_and_preserves_input_in_a_fresh_process():
    import json
    import os
    import subprocess
    import sys

    for experience, status, code in [("2–4 năm", "model_unavailable", 0), ("", "invalid_input", 2)]:
        profile = {
            "role": "Backend",
            "experience": experience,
            "skills": "Python",
            "location": "HCM",
            "work_mode": "Remote",
        }
        args = [sys.executable, "-m", "career_market", "predict"]
        for key, value in profile.items():
            args.extend(["--" + key.replace("_", "-"), value])
        completed = subprocess.run(
            args, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": "src"}
        )
        assert completed.returncode == code, completed.stderr
        result = json.loads(completed.stdout)
        assert result["status"] == status
        assert result == MarketService().predict_profile(profile)
        assert completed.stderr == ""
