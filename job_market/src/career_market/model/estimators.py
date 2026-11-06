"""BƯỚC 3a — Đặc trưng và định nghĩa mô hình.

Mục này làm gì: biến một tin/hồ sơ thành ma trận đặc trưng (vai trò, khu vực, cấp bậc,
kinh nghiệm, năm, 70 cột kỹ năng 0/1) và dựng 4 mô hình. Mọi mô hình học trên log(lương)
và bị ràng buộc "thêm kỹ năng không làm giảm lương".
"""

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ..data.dataset import skill_lists
from ..data.rules import SKILLS

CATEGORICAL = ["role", "region", "level"]
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
CURRENT_YEAR = 2026


def feature_frame(frame):
    """Biến bảng tin (hoặc hồ sơ người dùng) thành ma trận đặc trưng cố định."""
    skills = skill_lists(frame) if "skills" in frame else pd.Series([[]] * len(frame))
    features = frame[CATEGORICAL].copy()
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
