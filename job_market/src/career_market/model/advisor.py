"""BƯỚC 4 — Dự đoán lương cho một hồ sơ và gợi ý kỹ năng nên học.

Mục này làm gì: nạp mô hình đã lưu (không huấn luyện lại), dự đoán lương + khoảng 80%,
thử thêm từng kỹ năng để đo mức tăng lương, và vẽ lộ trình theo số năm kinh nghiệm.
"""

import pandas as pd

from ..data.dataset import load_dataset, skill_lists
from ..data.rules import SKILLS, derive_level
from .estimators import CURRENT_YEAR, MODEL_LABELS, SKILL_COLUMNS, feature_frame
from .training import load_model


def _profile_frame(profile):
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
            }
        ]
    )


def predict_profile(profile, model_name=None):
    model, name, report = load_model(model_name)
    value = float(model.predict(feature_frame(_profile_frame(profile)))[0])
    band = report["interval_ratio"]
    return {
        "model": name,
        "salary": value,
        "low": value * band["p10"],
        "high": value * band["p90"],
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
    band = report["interval_ratio"]
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
                "uplift": float(model.predict(changed)[0]) - base,
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
        future = {**profile, "experience_years": years + extra, "level": None}
        future_features = feature_frame(_profile_frame(future))
        path.append(
            {
                "experience_years": years + extra,
                "level": _profile_frame(future)["level"][0],
                "salary": float(model.predict(future_features)[0]),
            }
        )
    role_salaries = role_rows["salary"]
    return {
        "model": name,
        "model_label": MODEL_LABELS[name],
        "salary": base,
        "low": base * band["p10"],
        "high": base * band["p90"],
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
