"""Huấn luyện, đánh giá và tư vấn lương trên bộ dữ liệu mở rộng salary-v2.

Ba mô hình (Ridge, Random Forest, Gradient Boosting) cùng một mốc trung vị được
fit trên tập train, chọn siêu tham số và mô hình bằng tập valid, sau đó báo cáo
một lần trên tập test. Mục tiêu là log(lương) để giảm ảnh hưởng của lương rất cao.
"""

import functools
import json
import time
from itertools import combinations
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .prediction_support import build_support, resolve
from .salary_dataset import SKILLS, derive_level, load_dataset, skill_lists
from .training_labels import data_root

CATEGORICAL = ["role", "region", "level", "platform", "work_mode", "company_type"]
# Từ khóa chức danh mang thông tin lương ngoài cấp bậc (#81); hồ sơ không ghi chức danh = 0.
TITLE_FLAGS = {
    "title::expert": r"expert|chuyên gia",
    "title::principal": r"principal|staff engineer|chief",
    "title::head": r"head of|\bhead\b|giám đốc|director",
    "title::consultant": r"consultant|tư vấn",
}


@functools.lru_cache(maxsize=1)
def default_platform():
    """Nguồn đăng tin không có ở hồ sơ người dùng: dùng nền tảng phổ biến nhất của train."""
    frame = load_dataset()
    return frame.loc[frame["split"] == "train", "platform"].mode().iloc[0]


# Không dùng số lượng kỹ năng: tin liệt kê nhiều kỹ năng thường là tin tuyển junior/hàng
# loạt nên đặc trưng này dạy mô hình rằng "thêm kỹ năng thì lương giảm".
NUMERIC = ["experience_years", "year"]
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
    features = frame[["role", "region", "level"]].copy()
    features["platform"] = frame["platform"] if "platform" in frame else default_platform()
    features["work_mode"] = frame.get("work_mode", "Không rõ")
    features["company_type"] = frame.get("company_type", "Khác")
    titles = frame.get("title", pd.Series([""] * len(frame), index=frame.index)).fillna("")
    for column, pattern in TITLE_FLAGS.items():
        features[column] = titles.str.contains(pattern, case=False, regex=True).astype(int)
    features["experience_years"] = pd.to_numeric(frame["experience_years"], errors="coerce")
    features["year"] = frame.get("year", CURRENT_YEAR)
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
            ("title", "passthrough", list(TITLE_FLAGS)),
        ]
    )


class SignedRidge(RegressorMixin, BaseEstimator):
    """Ridge với hệ số các cột kỹ năng bị chặn >= 0 (thêm kỹ năng không làm giảm lương)."""

    def __init__(self, alpha=1.0, nonnegative_prefix="skills__"):
        self.alpha = alpha
        self.nonnegative_prefix = nonnegative_prefix

    def fit(self, X, y):
        names = list(getattr(X, "columns", range(np.shape(X)[1])))
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        x_mean, y_mean = X.mean(axis=0), y.mean()
        width = X.shape[1]
        design = np.vstack([X - x_mean, np.sqrt(self.alpha) * np.eye(width)])
        target = np.concatenate([y - y_mean, np.zeros(width)])
        lower = np.array(
            [0.0 if str(n).startswith(self.nonnegative_prefix) else -np.inf for n in names]
        )
        self.coef_ = lsq_linear(design, target, bounds=(lower, np.inf)).x
        self.intercept_ = float(y_mean - x_mean @ self.coef_)
        self.feature_names_in_ = np.array(names, dtype=object)
        self.n_features_in_ = width
        return self

    def predict(self, X):
        return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_


class SkillEnvelope(RegressorMixin, BaseEstimator):
    """Hậu xử lý đơn điệu cho mô hình không hỗ trợ ràng buộc (Random Forest).

    Dự đoán cho một bộ kỹ năng S là max của mô hình gốc trên mọi tập con của S, tức bao
    đơn điệu nhỏ nhất nằm trên mô hình: thêm kỹ năng không bao giờ làm dự đoán giảm.
    """

    def __init__(self, estimator):
        self.estimator = estimator

    def fit(self, X, y):
        self.estimator_ = clone(self.estimator).fit(X, y)
        return self

    def predict(self, X):
        skills = [c for c in X.columns if c.startswith("skill::")]
        owned = X[skills].to_numpy() > 0
        groups, cleared = [], []  # cleared: (vị trí dòng mở rộng, cột kỹ năng tắt)
        for index, mask in enumerate(owned):
            have = np.flatnonzero(mask)
            for size in range(len(have) + 1):
                for drop in combinations(have, size):
                    cleared.extend((len(groups), column) for column in drop)
                    groups.append(index)
        expanded = X.iloc[groups].reset_index(drop=True)
        if cleared:
            positions, columns = np.array(cleared).T
            values = expanded[skills].to_numpy(copy=True)
            values[positions, columns] = 0
            expanded[skills] = values
        predicted = self.estimator_.predict(expanded)
        return pd.Series(predicted).groupby(np.array(groups)).max().to_numpy()


def build_model(name, **params):
    if name == "Baseline":
        return DummyRegressor(strategy="median")
    if name == "Ridge":
        regressor, scale = SignedRidge(**params), True
    elif name == "RandomForest":
        regressor = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1, **params)
        scale = False
    elif name == "GradientBoosting":
        # Ràng buộc đơn điệu: thêm kinh nghiệm hoặc thêm kỹ năng không làm lương giảm.
        regressor = HistGradientBoostingRegressor(
            max_iter=500,
            early_stopping=False,
            l2_regularization=1.0,
            random_state=42,
            monotonic_cst={
                "numeric__experience_years": 1,
                **{f"skills__{column}": 1 for column in SKILL_COLUMNS},
            },
            **params,
        )
        scale = False
    else:
        raise ValueError(f"Không có mô hình {name}")
    preprocessor = _preprocessor(scale).set_output(transform="pandas")
    model = TransformedTargetRegressor(
        regressor=make_pipeline(preprocessor, regressor), func=np.log, inverse_func=np.exp
    )
    return SkillEnvelope(model) if name == "RandomForest" else model


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
    report["support"] = build_support(
        parts["train"], parts["valid"], model.predict(features["valid"])
    )
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


def load_production():
    """Bảng chấm chuẩn production của model đang phục vụ, hoặc None nếu chưa kiểm định."""
    path = artifacts_dir() / "validation.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("production")


def _supported(profile_frame, value, report, production):
    row = profile_frame.iloc[0]
    return {
        **resolve(row["role"], row["level"], value, report, production),
        "production_ready": bool(production and production["production_ready"]),
    }


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
                "title": profile.get("title") or "",
                "work_mode": profile.get("work_mode") or "Không rõ",
                "company_type": profile.get("company_type") or "Khác",
                "platform": default_platform(),
            }
        ]
    )


def predict_profile(profile, model_name=None):
    model, name, report = load_model(model_name)
    frame = _profile_frame(profile)
    value = float(model.predict(feature_frame(frame))[0])
    # "predicted" là đầu ra thô của mô hình (luôn có), dùng cho kiểm thử và phân tích;
    # "salary" là con số hiển thị, None khi hồ sơ ít dữ liệu.
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
    production = load_production()
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
        future_frame = _profile_frame(future)
        future_value = float(model.predict(feature_frame(future_frame))[0])
        step = _supported(future_frame, future_value, report, production)
        path.append(
            {
                "experience_years": years + extra,
                "level": future_frame["level"][0],
                "salary": step["salary"],
                "low": step["low"],
                "high": step["high"],
                "predicted": future_value,
            }
        )
    role_salaries = role_rows["salary"]
    return {
        "model": name,
        "model_label": MODEL_LABELS[name],
        **_supported(base_frame, base, report, production),
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
