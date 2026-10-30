"""Prediction demo uses the saved, validation-selected model without fitting."""

from career_market import MarketService


def test_supported_role_and_city_return_saved_model_salary_without_advice():
    result = MarketService().estimate_salary("Data/ML", "Hồ Chí Minh")
    assert result["status"] == "ok"
    assert result["salary_vnd_month"] > 0
    assert result["model"] == "Ridge"
    assert result["support_count"] == 3
    assert result["location"] == "HCM"
    assert "advice" not in result


def test_unsupported_role_does_not_fabricate_a_salary():
    result = MarketService().estimate_salary("Backend", "HN")
    assert result["status"] == "unsupported"
    assert result["salary_vnd_month"] is None


def test_cli_predict_uses_same_model_in_fresh_process():
    import json
    import os
    import subprocess
    import sys

    for role, location, code in [
        ("Data/ML", "HN", 0),
        ("Backend", "HN", 0),
        ("astronaut", "HN", 2),
    ]:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "career_market",
                "predict",
                "--role",
                role,
                "--location",
                location,
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
        )
        assert result.returncode == code, result.stderr
        assert json.loads(result.stdout) == MarketService().estimate_salary(role, location)
