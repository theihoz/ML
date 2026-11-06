"""BƯỚC 4 — Dự đoán lương cho một hồ sơ và gợi ý kỹ năng nên học.

Mục này làm gì: nạp mô hình đã lưu (không huấn luyện lại), dự đoán khoảng lương p25–trung vị–p75,
thử thêm từng kỹ năng để đo mức tăng lương, và vẽ lộ trình theo số năm kinh nghiệm.
"""

import pandas as pd

from ..data.dataset import load_dataset, skill_lists
from ..data.rules import LEVELS, SKILLS, derive_level
from .calibration import calibration_for, load_calibration
from .estimators import CURRENT_YEAR, MODEL_LABELS, SKILL_COLUMNS, default_platform, feature_frame
from .support import resolve
from .training import load_model, load_production

PRIORITY_CITIES = {"Hà Nội", "TP. Hồ Chí Minh"}
PRIORITY_ROLES = {
    "Backend Developer",
    "Frontend Developer",
    "Fullstack Developer",
    "Mobile Developer",
    "Kiểm thử (QA/QC)",
    "DevOps / Cloud",
    "Data Engineer",
    "Data Analyst / BI",
    "AI / ML Engineer",
    "Business Analyst",
}  # Data/AI gồm ba vai trò chi tiết trong bộ dữ liệu.


def data_sufficiency(profile, frame, level):
    """Hồ sơ có đủ dữ liệu không: trong vùng ưu tiên và nhóm có ít nhất 20 tin học."""
    in_priority = (
        profile.get("region", "Hà Nội") in PRIORITY_CITIES and profile["role"] in PRIORITY_ROLES
    )
    cohort = frame[
        (frame["split"] == "train")
        & (frame["role"] == profile["role"])
        & (frame["region"] == profile.get("region", "Hà Nội"))
        & (frame["level"] == level)
    ]
    warnings = []
    if not in_priority:
        warnings.append("Ngoài vùng ưu tiên; ít dữ liệu, chỉ nên tham khảo.")
    if len(cohort) < 20:
        warnings.append("Nhóm vai trò × cấp bậc × thành phố có dưới 20 tin huấn luyện.")
    return {
        "in_priority": in_priority,
        "thin_cohort": len(cohort) < 20,
        "train_postings": len(cohort),
        "warnings": warnings,
    }


def _profile_frame(profile):
    """Biến hồ sơ người dùng nhập thành một dòng dữ liệu giống một tin tuyển dụng."""
    years = profile.get("experience_years")
    level = profile.get("level") or derive_level("", years)
    return pd.DataFrame(
        [
            {
                "role": profile["role"],
                "region": profile.get("region", "Hà Nội"),
                "level": level,
                "experience_years": years,
                "year": CURRENT_YEAR,
                "skills": "|".join(profile.get("skills", [])),
                "title": profile.get("title") or "",
                "work_mode": profile.get("work_mode") or "Không rõ",
                "company_type": profile.get("company_type") or "Khác",
                "platform": default_platform(),
            }
        ]
    )


def _supported(profile_frame, value, report, production):
    """Mức hỗ trợ dữ liệu (#89): con số chỉ hiện khi nhóm vai trò × cấp bậc đủ tin train
    và không trượt chuẩn production; nếu không, chỉ có khoảng mở rộng."""
    row = profile_frame.iloc[0]
    return {
        **resolve(row["role"], row["level"], value, report, production),
        "production_ready": bool(production and production["production_ready"]),
    }


def predict_profile(profile, model_name=None):
    """Đầu ra thô của mô hình (lương chào tuyển) kèm mức hỗ trợ dữ liệu.

    "predicted" luôn có, dùng cho kiểm thử và phân tích; "salary" là con số hiển thị,
    None khi hồ sơ ít dữ liệu.
    """
    model, name, report = load_model(model_name)
    frame = _profile_frame(profile)
    value = float(model.predict(feature_frame(frame))[0])
    return {
        "model": name,
        "predicted": value,
        **_supported(frame, value, report, load_production()),
    }


def advise(profile, model_name=None, top_k=5, min_share=0.03):
    """Dự đoán lương cho hồ sơ và đề xuất kỹ năng nên học thêm.

    Kỹ năng ứng viên là kỹ năng xuất hiện ở ít nhất ``min_share`` số tin của cùng vai
    trò mà người dùng chưa có. Mỗi kỹ năng được chấm bằng mức tăng lương mô hình dự
    đoán khi thêm đúng kỹ năng đó vào hồ sơ, kèm mức độ được nhà tuyển dụng yêu cầu.
    """
    model, name, report = load_model(model_name)
    frame = load_dataset()
    base_frame = _profile_frame(profile)
    base_features = feature_frame(base_frame)
    base = float(model.predict(base_features)[0])
    band = report["models"][name]["interval_ratio"]
    salary_range = {
        "p25": base * band["p25"],
        "median": base * band["p50"],
        "p75": base * band["p75"],
    }
    advertised_range = salary_range.copy()
    table = load_calibration(name)
    calibration = calibration_for(
        table, base_frame["level"][0], base_frame["region"][0], profile["role"]
    )
    salary_range = {key: value * calibration["factor"] for key, value in advertised_range.items()}
    production = load_production()
    support = _supported(base_frame, base, report, production)
    role_rows = frame[frame["role"] == profile["role"]]
    role_skills = skill_lists(role_rows)
    owned = set(profile.get("skills", []))
    # Mục này: thử bật từng kỹ năng chưa có → đo lương dự đoán tăng bao nhiêu.
    candidates = []
    for skill, column in zip(SKILLS, SKILL_COLUMNS):
        if skill in owned or not len(role_rows):
            continue
        share = float(role_skills.map(lambda skills, skill=skill: skill in skills).mean())
        if share < min_share:
            continue
        changed = base_features.copy()
        changed[column] = 1
        candidates.append(
            {
                "skill": skill,
                "uplift": (float(model.predict(changed)[0]) - base)
                * band["p50"]
                * calibration["factor"],
                "demand_share": share,
            }
        )
    # Ưu tiên kỹ năng mô hình thấy làm tăng lương; nếu chưa đủ, bổ sung kỹ năng được
    # yêu cầu nhiều nhất cho vai trò để người dùng vẫn có định hướng học tập.
    gaining = sorted(
        (row for row in candidates if row["uplift"] > 0.1),
        key=lambda row: (row["uplift"], row["demand_share"]),
        reverse=True,
    )
    popular = sorted(
        (row for row in candidates if row not in gaining),
        key=lambda row: row["demand_share"],
        reverse=True,
    )
    for row in gaining:
        row["reason"] = "Tăng lương dự đoán"
    for row in popular:
        row["reason"] = "Được yêu cầu nhiều"
    candidates = gaining + popular
    years = profile.get("experience_years") or 0
    # Mục này: lộ trình — dự đoán lại khi thêm 0/1/2/3/5 năm kinh nghiệm.
    path = []
    for extra in (0, 1, 2, 3, 5):
        current_level = base_frame["level"][0]
        inferred = derive_level("", years + extra)
        future_level = (
            current_level
            if extra == 0
            else LEVELS[max(LEVELS.index(current_level), LEVELS.index(inferred))]
        )
        future = {**profile, "experience_years": years + extra, "level": future_level}
        future_frame = _profile_frame(future)
        future_value = float(model.predict(feature_frame(future_frame))[0])
        factor = calibration_for(table, future_level, base_frame["region"][0], profile["role"])[
            "factor"
        ]
        step = _supported(future_frame, future_value, report, production)
        median = future_value * band["p50"] * factor
        path.append(
            {
                "experience_years": years + extra,
                "level": future_level,
                # Nhóm ít dữ liệu: không vẽ con số, chỉ vẽ khoảng mở rộng (#89).
                "salary": median if step["supported"] else None,
                "low": future_value * band["p25"] * factor
                if step["supported"]
                else step["low"] * factor,
                "high": future_value * band["p75"] * factor
                if step["supported"]
                else step["high"] * factor,
                "predicted": future_value,
            }
        )
    role_salaries = role_rows["salary"]
    return {
        "model": name,
        "model_label": MODEL_LABELS[name],
        # Con số hiển thị: trung vị lương thị trường khi đủ dữ liệu; None khi ít dữ liệu,
        # khi đó low/high là khoảng mở rộng (#89) đã nhân hệ số gross.
        "salary": salary_range["median"] if support["supported"] else None,
        "low": salary_range["p25"]
        if support["supported"]
        else support["low"] * calibration["factor"],
        "high": salary_range["p75"]
        if support["supported"]
        else support["high"] * calibration["factor"],
        "predicted": base,
        "supported": support["supported"],
        "support_reasons": support["support_reasons"],
        "support_message": support["support_message"],
        "cohort_rows": support["cohort_rows"],
        "production_ready": support["production_ready"],
        "salary_range": salary_range,
        "market_range": salary_range,
        "advertised_range": advertised_range,
        "calibration": calibration,
        "data_sufficiency": data_sufficiency(profile, frame, base_frame["level"][0]),
        "level": base_frame["level"][0],
        "recommendations": candidates[:top_k],
        "experience_path": path,
        "market": {
            "role_postings": int(len(role_rows)),
            "role_median": float(role_salaries.median()) if len(role_rows) else None,
            "role_p25": float(role_salaries.quantile(0.25)) if len(role_rows) else None,
            "role_p75": float(role_salaries.quantile(0.75)) if len(role_rows) else None,
            "percentile": float((role_salaries < base).mean() * 100) if len(role_rows) else None,
        },
        "test_mae": report["models"][name]["test"]["MAE"],
    }
