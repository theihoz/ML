"""Salary-only academic demo using the saved pipeline for valid role/city queries."""

import math

from .roles import ROLE_PATTERNS
from .training import default_runs, features, load_run


def estimate_salary(service, role, location, model_name=None):
    empty = {"salary_vnd_month": None}
    if not isinstance(role, str) or not isinstance(location, str):
        return {**empty, "status": "invalid_input", "message": "Chọn nghề và thành phố."}
    if model_name is not None and model_name not in {"Ridge", "LinearRegression"}:
        return {**empty, "status": "invalid_input", "message": "Chọn mô hình hợp lệ."}
    role = next(
        (name for name in ROLE_PATTERNS if name.casefold() == role.strip().casefold()), None
    )
    places = service.normalize_locations(location)
    if (
        role is None
        or len(places["locations"]) != 1
        or places["location_unresolved"]
        or places["work_modes"]
    ):
        return {
            **empty,
            "status": "invalid_input",
            "message": "Chọn một nghề và một thành phố hợp lệ.",
        }
    city = places["locations"][0]
    run = load_run(default_runs() / "7137291a5d16b71f1861", model_name=model_name)
    report = run["report"]
    if not report["promoted"]:
        return {
            **empty,
            "status": "model_unavailable",
            "message": "Mô hình chưa đạt điều kiện dự đoán.",
        }
    role_rows = [row for row in run["train"] if row["role"] == role]
    local_rows = [row for row in role_rows if city in row["locations"]]
    # Academic demo: no minimum-sample gate. DictVectorizer keeps the frozen
    # vocabulary and ignores unseen category keys; no retraining or city mean.
    # This is explicitly a role/city query with other fields unobserved, exactly
    # the missing-feature representation of the frozen training cohort.
    query = {
        "role": role,
        "locations": [city],
        "skills": [],
        "work_modes": [],
        "experience_min": None,
        "experience_max": None,
        "experience_kind": "missing",
    }
    salary = float(run["model"].predict([features(query)])[0]) * 1000000
    if not math.isfinite(salary) or salary <= 0:
        return {
            **empty,
            "status": "unsupported",
            "message": "Chưa có ước tính phù hợp cho lựa chọn này.",
        }
    return {
        "status": "ok",
        "salary_vnd_month": salary,
        "role": role,
        "location": city,
        "model": run["prediction_model"],
        "run_id": report["run_id"],
        "support_count": len(local_rows),
        "dataset_count": report["source_entities"],
        "test_mae_vnd_month": report["metrics"][run["prediction_model"]]["test"]["MAE"],
        "cohort": report["cohort"],
        "scope": "role_and_city_only",
    }
