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


def test_all_demo_roles_and_cities_use_the_saved_model_without_sample_gate():
    service = MarketService()
    for role in (
        "Backend",
        "Frontend",
        "Fullstack",
        "Mobile",
        "DevOps",
        "QA Automation",
        "Data/ML",
    ):
        for city in ("HN", "HCM", "Đà Nẵng"):
            for model in ("Ridge", "LinearRegression"):
                result = service.estimate_salary(role, city, model_name=model)
                assert result["status"] == "ok", (role, city, model, result)
                assert result["salary_vnd_month"] > 0
                assert result["model"] == model


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


def test_user_can_switch_between_both_saved_models_without_retraining():
    service = MarketService()
    ridge = service.estimate_salary("Data/ML", "HN", model_name="Ridge")
    linear = service.estimate_salary("Data/ML", "HN", model_name="LinearRegression")
    assert ridge["model"] == "Ridge"
    assert linear["model"] == "LinearRegression"
    assert ridge["salary_vnd_month"] != linear["salary_vnd_month"]
    assert ridge["run_id"] == linear["run_id"]
    assert round(linear["test_mae_vnd_month"]) == 17576149
    assert round(ridge["test_mae_vnd_month"]) == 21975802
