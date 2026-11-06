"""BƯỚC 3b — Huấn luyện, chọn mô hình và lưu kết quả.

Mục này làm gì: fit 4 mô hình trên train, dò siêu tham số bằng valid, chọn mô hình có
MAE valid nhỏ nhất, báo cáo một lần trên test, rồi lưu .joblib + metrics.json.
"""

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)

from ..data.dataset import load_dataset, skill_lists
from ..data.rules import SKILLS
from ..paths import artifacts_dir
from .estimators import MODEL_LABELS, SKILL_COLUMNS, build_model, feature_frame
from .support import build_support

# Lưới siêu tham số thử trên tập valid.

GRID = {
    "Ridge": [{"alpha": a} for a in (0.3, 1.0, 3.0, 10.0)],
    "RandomForest": [{"min_samples_leaf": leaf} for leaf in (1, 3, 5)],
    "GradientBoosting": [
        {"learning_rate": lr, "max_leaf_nodes": leaves} for lr in (0.05, 0.1) for leaves in (15, 31)
    ],
}


def scores(actual, predicted):
    """Bốn chỉ số sai số: MAE, RMSE, R², MAPE (xem docs/kien-thuc-du-an/04-cong-thuc.md)."""
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
    # Mục này: với mỗi mô hình, thử từng bộ siêu tham số, giữ bộ có MAE valid nhỏ nhất.
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
        ratio = targets["valid"] / best["model"].predict(features["valid"])
        report["models"][name]["interval_ratio"] = {
            f"p{q}": float(np.quantile(ratio, q / 100)) for q in (10, 25, 50, 75, 90)
        }
        joblib.dump(best["model"], output / f"{name}.joblib", compress=3)
    # Mục này: chọn mô hình tốt nhất theo valid (test chỉ để báo cáo).
    candidates = [name for name in report["models"] if name != "Baseline"]
    selected = min(candidates, key=lambda name: report["models"][name]["valid"]["MAE"])
    report["selected"] = selected
    model = fitted[selected]
    # Phân vị thực nghiệm: tỉ lệ lương thật / dự đoán trên tập valid.
    report["interval_ratio"] = report["models"][selected]["interval_ratio"].copy()
    # Mức hỗ trợ dữ liệu theo vai trò × cấp bậc và khoảng mở rộng cho hồ sơ ít dữ liệu (#89).
    report["support"] = build_support(
        parts["train"], parts["valid"], model.predict(features["valid"])
    )
    # Mục này: lưu dự đoán test, sai số theo vai trò, độ quan trọng đặc trưng, giá trị kỹ năng.
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
    from .calibration import build_calibration

    build_calibration(frame, fitted, report, output)
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
    """Đọc báo cáo huấn luyện (metrics.json) của phiên bản đang phục vụ."""
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


def load_model(name=None):
    """Nạp một mô hình đã lưu (mặc định: mô hình được chọn)."""
    report = load_report()
    name = name or report["selected"]
    return joblib.load(artifacts_dir() / f"{name}.joblib"), name, report


def load_skill_value():
    """Đọc bảng giá trị gia tăng của từng kỹ năng."""
    return pd.read_csv(artifacts_dir() / "skill_value.csv")
