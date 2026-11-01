"""Huấn luyện, đánh giá và tư vấn lương trên bộ dữ liệu mở rộng salary-v2.

Ba mô hình (Ridge, Random Forest, Gradient Boosting) cùng một mốc trung vị được
fit trên tập train, chọn siêu tham số và mô hình bằng tập valid, sau đó báo cáo
một lần trên tập test. Mục tiêu là log(lương) để giảm ảnh hưởng của lương rất cao.
"""

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .salary_dataset import SKILLS, derive_level, load_dataset, skill_lists
from .training_labels import data_root

CATEGORICAL = ["role", "region", "level"]
NUMERIC = ["experience_years", "year", "skill_count"]
SKILL_COLUMNS = [f"skill::{name}" for name in SKILLS]
MODEL_LABELS = {
    "Baseline": "Mốc trung vị",
    "Ridge": "Ridge Regression",
    "RandomForest": "Random Forest",
    "GradientBoosting": "Gradient Boosting",
}
GRID = {
    "Ridge": [{"alpha": a} for a in (0.3, 1.0, 3.0, 10.0)],
    "RandomForest": [{"min_samples_leaf": leaf} for leaf in (1, 3, 5)],
    "GradientBoosting": [
        {"learning_rate": lr, "max_leaf_nodes": leaves} for lr in (0.05, 0.1) for leaves in (15, 31)
    ],
}
CURRENT_YEAR = 2026


def artifacts_dir():
    return data_root().parent / "artifacts/salary-v2"


def feature_frame(frame):
    """Biến bảng tin (hoặc hồ sơ người dùng) thành ma trận đặc trưng cố định."""
    skills = skill_lists(frame) if "skills" in frame else pd.Series([[]] * len(frame))
    features = frame[CATEGORICAL].copy()
    features["experience_years"] = pd.to_numeric(frame["experience_years"], errors="coerce")
    features["year"] = frame.get("year", CURRENT_YEAR)
    features["skill_count"] = skills.map(len)
    for name, column in zip(SKILLS, SKILL_COLUMNS):
        features[column] = skills.map(lambda owned, name=name: int(name in owned))
    return features


def _preprocessor(scale):
    numeric = [SimpleImputer(strategy="median", add_indicator=True)]
    if scale:
        numeric.append(StandardScaler())
    return ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
            ("numeric", make_pipeline(*numeric), NUMERIC),
            ("skills", "passthrough", SKILL_COLUMNS),
        ]
    )


def build_model(name, **params):
    if name == "Baseline":
        return DummyRegressor(strategy="median")
    if name == "Ridge":
        regressor, scale = Ridge(**params), True
    elif name == "RandomForest":
        regressor = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1, **params)
        scale = False
    elif name == "GradientBoosting":
        # Ràng buộc đơn điệu: thêm kinh nghiệm không làm lương dự đoán giảm.
        regressor = HistGradientBoostingRegressor(
            max_iter=500,
            early_stopping=False,
            l2_regularization=1.0,
            random_state=42,
            monotonic_cst={"numeric__experience_years": 1},
            **params,
        )
        scale = False
    else:
        raise ValueError(f"Không có mô hình {name}")
    preprocessor = _preprocessor(scale).set_output(transform="pandas")
    return TransformedTargetRegressor(
        regressor=make_pipeline(preprocessor, regressor), func=np.log, inverse_func=np.exp
    )


def scores(actual, predicted):
    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "RMSE": float(np.sqrt(mean_squared_error(actual, predicted))),
        "R2": float(r2_score(actual, predicted)),
        "MAPE": float(mean_absolute_percentage_error(actual, predicted) * 100),
        "n": int(len(actual)),
    }


def train(output=None):
    """Fit toàn bộ mô hình, chọn theo valid MAE, lưu artifact và trả về báo cáo."""
    output = Path(output) if output else artifacts_dir()
    output.mkdir(parents=True, exist_ok=True)
    frame = load_dataset()
    parts = {name: frame[frame["split"] == name] for name in ("train", "valid", "test")}
    features = {name: feature_frame(part) for name, part in parts.items()}
    targets = {name: part["salary"].to_numpy() for name, part in parts.items()}
    report = {"dataset_rows": len(frame), "split": {k: len(v) for k, v in parts.items()}}
    report["models"], report["tuning"], fitted = {}, {}, {}
    for name in ["Baseline", *GRID]:
        trials = []
        for params in GRID.get(name, [{}]):
            started = time.perf_counter()
            model = build_model(name, **params).fit(features["train"], targets["train"])
            valid = scores(targets["valid"], model.predict(features["valid"]))
            trials.append(
                {
                    "params": params,
                    "valid": valid,
                    "fit_seconds": time.perf_counter() - started,
                    "model": model,
                }
            )
        best = min(trials, key=lambda trial: trial["valid"]["MAE"])
        fitted[name] = best["model"]
        report["tuning"][name] = [
            {"params": t["params"], "valid_MAE": t["valid"]["MAE"]} for t in trials
        ]
        report["models"][name] = {
            "label": MODEL_LABELS[name],
            "params": best["params"],
            "fit_seconds": best["fit_seconds"],
            **{
                part: scores(targets[part], best["model"].predict(features[part]))
                for part in ("train", "valid", "test")
            },
        }
        joblib.dump(best["model"], output / f"{name}.joblib", compress=3)
    candidates = [name for name in report["models"] if name != "Baseline"]
    selected = min(candidates, key=lambda name: report["models"][name]["valid"]["MAE"])
    report["selected"] = selected
    model = fitted[selected]
    # Dải tin cậy thực nghiệm: tỉ lệ lương thật / dự đoán trên tập valid.
    ratio = targets["valid"] / model.predict(features["valid"])
    report["interval_ratio"] = {
        "p10": float(np.quantile(ratio, 0.10)),
        "p90": float(np.quantile(ratio, 0.90)),
    }
    test_frame = parts["test"].assign(predicted=model.predict(features["test"]))
    test_frame["abs_error"] = (test_frame["predicted"] - test_frame["salary"]).abs()
    test_frame[
        ["row_id", "title", "role", "region", "level", "experience_years", "salary", "predicted"]
        + ["abs_error"]
    ].to_csv(output / "test_predictions.csv", index=False)
    report["test_by_role"] = (
        test_frame.groupby("role")["abs_error"].agg(["mean", "count"]).round(3).to_dict("index")
    )
    importance = permutation_importance(
        model, features["valid"], targets["valid"], n_repeats=5, random_state=42, n_jobs=-1
    )
    report["permutation_importance"] = (
        pd.Series(importance.importances_mean, index=features["valid"].columns)
        .sort_values(ascending=False)
        .head(20)
        .round(4)
        .to_dict()
    )
    skill_value(frame, model).to_csv(output / "skill_value.csv", index=False)
    (output / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def skill_value(frame, model, min_postings=20):
    """Giá trị gia tăng của từng kỹ năng theo hai góc nhìn.

    * premium_median: chênh trung vị lương giữa tin có và không nhắc kỹ năng (mô tả).
    * model_uplift: mức tăng dự đoán trung bình khi bật kỹ năng cho các tin chưa có
      nó, giữ nguyên vai trò, kinh nghiệm và địa điểm (ceteris paribus).
    """
    owned = skill_lists(frame)
    base_features = feature_frame(frame)
    base = model.predict(base_features)
    rows = []
    for name, column in zip(SKILLS, SKILL_COLUMNS):
        has = owned.map(lambda skills, name=name: name in skills)
        if has.sum() < min_postings:
            continue
        lacking = ~has
        changed = base_features[lacking].copy()
        changed[column] = 1
        changed["skill_count"] += 1
        uplift = model.predict(changed) - base[lacking.to_numpy()]
        rows.append(
            {
                "skill": name,
                "postings": int(has.sum()),
                "median_with": float(frame.loc[has, "salary"].median()),
                "median_without": float(frame.loc[lacking, "salary"].median()),
                "premium_median": float(
                    frame.loc[has, "salary"].median() - frame.loc[lacking, "salary"].median()
                ),
                "model_uplift": float(uplift.mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("model_uplift", ascending=False)


def load_report():
    path = artifacts_dir() / "metrics.json"
    if not path.exists():
        return train()
    return json.loads(path.read_text(encoding="utf-8"))


def load_model(name=None):
    report = load_report()
    name = name or report["selected"]
    return joblib.load(artifacts_dir() / f"{name}.joblib"), name, report


def load_skill_value():
    return pd.read_csv(artifacts_dir() / "skill_value.csv")


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
    candidates = []
    for skill, column in zip(SKILLS, SKILL_COLUMNS):
        if skill in owned or not len(role_rows):
            continue
        share = float(role_skills.map(lambda skills, skill=skill: skill in skills).mean())
        if share < min_share:
            continue
        changed = base_features.copy()
        changed[column] = 1
        changed["skill_count"] += 1
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
