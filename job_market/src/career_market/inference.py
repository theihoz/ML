"""Salary-only demo for supported role/city queries; never fit or recommend skills."""

import math

from .companies import canonical_name
from .roles import ROLE_PATTERNS
from .training import default_runs, features, load_run


def estimate_salary(service, role, location):
    empty = {"salary_vnd_month": None}
    if not isinstance(role, str) or not isinstance(location, str):
        return {**empty, "status": "invalid_input", "message": "Chọn nghề và thành phố."}
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
    run = load_run(default_runs() / "7137291a5d16b71f1861")
    report, policy = run["report"], run["policy"]
    if not report["promoted"]:
        return {
            **empty,
            "status": "model_unavailable",
            "message": "Mô hình chưa đạt điều kiện dự đoán.",
        }
    role_rows = [row for row in run["train"] if row["role"] == role]
    local_rows = [row for row in role_rows if city in row["locations"]]
    companies = {canonical_name(row["company_raw"]) for row in role_rows}
    support = policy["support"]
    if (
        len(role_rows) < support["role_entities"]
        or len(companies) < support["role_companies"]
        or len(local_rows) < support["location_entities"]
    ):
        return {
            **empty,
            "status": "unsupported",
            "message": "Nghề và thành phố này chưa đủ dữ liệu để dự đoán.",
            "role": role,
            "location": city,
        }
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
        "model": report["chosen_model"],
        "run_id": report["run_id"],
        "support_count": len(local_rows),
        "dataset_count": report["source_entities"],
        "test_mae_vnd_month": report["metrics"][report["chosen_model"]]["test"]["MAE"],
        "cohort": report["cohort"],
        "scope": "role_and_city_only",
    }
