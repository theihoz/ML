"""BƯỚC 5 — Kiểm định mô hình đã chọn trên tập test.

Mục này làm gì: (1) hiệu chuẩn — khoảng 80% có thật chứa ~80% tin không; (2) bootstrap
theo công ty — chênh MAE giữa các mô hình có chắc chắn không; (3) công bằng — mô hình
có lệch hệ thống theo khu vực, cấp bậc, nền tảng, vai trò không.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ..data.dataset import load_dataset
from ..paths import artifacts_dir
from .estimators import MODEL_LABELS, feature_frame
from .production import assess

LEVELS = (0.5, 0.8, 0.9)
RELIABILITY_LEVELS = tuple(round(float(x), 2) for x in np.arange(0.1, 1.0, 0.05))
BOOTSTRAP_ROUNDS = 1000
SEED = 42
MIN_GROUP = 20
EXPERIENCE_GROUPS = ([-0.1, 1.9, 4.9, 30], ["0–1 năm", "2–4 năm", "5+ năm"])
FAIRNESS_GROUPS = {
    "region": "Khu vực",
    "level": "Cấp bậc",
    "experience_group": "Kinh nghiệm",
    "platform": "Nền tảng nguồn",
    "role": "Vai trò",
}


def _predictions(directory=None):
    directory = Path(directory) if directory else artifacts_dir()
    frame = load_dataset()
    report = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
    parts = {
        name: frame[frame["split"] == name].reset_index(drop=True) for name in ("valid", "test")
    }
    predictions = {}
    for name in report["models"]:
        model = joblib.load(directory / f"{name}.joblib")
        predictions[name] = {
            part: model.predict(feature_frame(rows)) for part, rows in parts.items()
        }
    return parts, predictions, report


def interval_ratios(actual, predicted, level):
    """Phân vị của tỉ lệ thật/dự đoán trên valid: khoảng dự đoán = ŷ × [thấp, cao]."""
    ratio = actual / predicted
    tail = (1 - level) / 2
    return float(np.quantile(ratio, tail)), float(np.quantile(ratio, 1 - tail))


def calibration(valid, valid_pred, test, test_pred):
    rows, by_role, by_band = [], [], []
    for level in RELIABILITY_LEVELS:
        low, high = interval_ratios(valid["salary"].to_numpy(), valid_pred, level)
        inside = (test["salary"] >= test_pred * low) & (test["salary"] <= test_pred * high)
        rows.append(
            {
                "level": level,
                "coverage": float(inside.mean()),
                "low_ratio": low,
                "high_ratio": high,
                "mean_width": float((test_pred * (high - low)).mean()),
            }
        )
    low, high = interval_ratios(valid["salary"].to_numpy(), valid_pred, 0.8)
    covered = test.assign(
        inside=(test["salary"] >= test_pred * low) & (test["salary"] <= test_pred * high),
        band=pd.qcut(test["salary"], 3, labels=["Thấp", "Trung bình", "Cao"]),
    )
    for role, group in covered.groupby("role"):
        by_role.append({"group": role, "n": len(group), "coverage": float(group["inside"].mean())})
    for band, group in covered.groupby("band", observed=True):
        by_band.append(
            {
                "group": str(band),
                "n": len(group),
                "range": f"{group['salary'].min():.1f}–{group['salary'].max():.1f}",
                "coverage": float(group["inside"].mean()),
            }
        )
    return {
        "reliability": rows,
        "levels": [row for row in rows if row["level"] in LEVELS],
        "by_role": sorted(by_role, key=lambda row: row["coverage"]),
        "by_salary_band": by_band,
    }


def _metrics(actual, predicted):
    error = predicted - actual
    total = ((actual - actual.mean()) ** 2).sum()
    return {
        "MAE": float(np.abs(error).mean()),
        "RMSE": float(np.sqrt((error**2).mean())),
        "R2": float(1 - (error**2).sum() / total) if total > 0 else float("nan"),
    }


def _company_samples(test, rounds, seed):
    rng = np.random.default_rng(seed)
    groups = [idx.to_numpy() for _, idx in test.groupby("company_key").groups.items()]
    for _ in range(rounds):
        chosen = rng.integers(0, len(groups), len(groups))
        yield np.concatenate([groups[i] for i in chosen])


def _interval(values):
    values = np.asarray(values, dtype=float)
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def bootstrap(test, predictions, selected, rounds=BOOTSTRAP_ROUNDS, seed=SEED):
    """Lấy mẫu lại theo công ty: tin của cùng công ty luôn đi cùng nhau."""
    actual = test["salary"].to_numpy()
    samples = {name: {"MAE": [], "RMSE": [], "R2": []} for name in predictions}
    for index in _company_samples(test, rounds, seed):
        for name, preds in predictions.items():
            for key, value in _metrics(actual[index], preds["test"][index]).items():
                samples[name][key].append(value)
    result = {"rounds": rounds, "companies": int(test["company_key"].nunique()), "models": {}}
    for name, values in samples.items():
        result["models"][name] = {
            key: {"point": _metrics(actual, predictions[name]["test"])[key], "ci95": _interval(v)}
            for key, v in values.items()
        }
    result["differences"] = {}
    best = np.asarray(samples[selected]["MAE"])
    for name in predictions:
        if name == selected:
            continue
        diff = best - np.asarray(samples[name]["MAE"])
        result["differences"][name] = {
            "mean": float(diff.mean()),
            "ci95": _interval(diff),
            "p_better": float((diff < 0).mean()),
            "samples": [round(float(x), 4) for x in diff],
        }
    return result


PLATFORMS = {
    "vietnamworks": "VietnamWorks",
    "topcv": "TopCV",
    "careerviet": "CareerViet",
    "itviec": "ITviec",
}


def _platform(source):
    """Nền tảng gốc; bộ TopCV 2026 tách riêng vì chỉ có tiêu đề, không có mô tả."""
    if "(" in source:
        name = source.split("(")[-1].rstrip(")")
        return PLATFORMS.get(name, name)
    return {"TopCV 2026": "TopCV (bộ 2026)", "CareerBuilder 2023": "CareerBuilder"}.get(
        source, source
    )


def fairness(test, predicted, rounds=BOOTSTRAP_ROUNDS, seed=SEED):
    """Sai số và độ lệch (dự đoán − thật) theo nhóm, kèm khoảng tin cậy bootstrap."""
    data = test.assign(
        predicted=predicted,
        error=predicted - test["salary"].to_numpy(),
        platform=test["source"].map(_platform),
        experience_group=pd.cut(
            test["experience_years"], bins=EXPERIENCE_GROUPS[0], labels=EXPERIENCE_GROUPS[1]
        ).astype(str),
    )
    data["abs_error"] = data["error"].abs()
    data["pct_error"] = data["error"] / data["salary"] * 100
    samples = list(_company_samples(test, rounds, seed))
    result = {}
    for column, label in FAIRNESS_GROUPS.items():
        rows = []
        for value, group in data.groupby(column):
            members = set(group.index)
            boot_bias, boot_mae = [], []
            for index in samples:
                picked = [i for i in index if i in members]
                if picked:
                    boot_bias.append(data.loc[picked, "pct_error"].mean())
                    boot_mae.append(data.loc[picked, "abs_error"].mean())
            rows.append(
                {
                    "group": str(value),
                    "n": len(group),
                    "enough": len(group) >= MIN_GROUP,
                    "MAE": float(group["abs_error"].mean()),
                    "MAPE": float((group["abs_error"] / group["salary"]).mean() * 100),
                    "bias_pct": float(group["pct_error"].mean()),
                    "bias_pct_ci95": _interval(boot_bias),
                    "MAE_ci95": _interval(boot_mae),
                }
            )
        enough = [row for row in rows if row["enough"]]
        result[column] = {
            "label": label,
            "groups": sorted(rows, key=lambda row: -row["n"]),
            "mape_gap": (
                float(max(r["MAPE"] for r in enough) - min(r["MAPE"] for r in enough))
                if len(enough) > 1
                else None
            ),
        }
    return result


def gender_audit(frame):
    counts = frame["gender_requirement"].value_counts().to_dict()
    restricted = frame[frame["gender_requirement"] != "Không đề cập"]
    return {
        "counts": counts,
        "mentioned": int(len(restricted)),
        "share_pct": float(len(restricted) / len(frame) * 100),
        "examples": restricted[["title", "source", "gender_requirement", "salary"]].to_dict(
            "records"
        ),
        "used_as_feature": False,
    }


def latest_batch(parts, predicted):
    """Chỉ số phụ (#106): sai số của model trên tin của lô nhập mới nhất (valid + test).

    Tin của lô mới thuộc công ty đã ở train thì nằm ở train nên không được chấm ở đây.
    """
    rows = pd.concat([parts["valid"], parts["test"]], ignore_index=True)
    values = np.concatenate([predicted["valid"], predicted["test"]])
    batches = rows.get("batch", pd.Series("", index=rows.index)).fillna("").astype(str)
    if not (batches != "").any():
        return {"status": "chưa có lô mới", "batch": None, "n": 0}
    batch = max(batches[batches != ""])
    mask = (batches == batch).to_numpy()
    if not mask.any():
        return {"status": "lô mới không có tin valid/test", "batch": batch, "n": 0}
    actual = rows.loc[mask, "salary"].to_numpy(dtype=float)
    error_pct = np.abs(values[mask] - actual) / actual * 100
    return {
        "status": "đã chấm",
        "batch": batch,
        "n": int(mask.sum()),
        "MAE": float(np.mean(np.abs(values[mask] - actual))),
        "median_error_pct": float(np.median(error_pct)),
    }


def validate(output=None, rounds=BOOTSTRAP_ROUNDS, directory=None):
    """Kiểm định model đã lưu trong ``directory`` (mặc định: model đang phục vụ)."""
    parts, predictions, report = _predictions(directory)
    selected = report["selected"]
    valid, test = parts["valid"], parts["test"]
    result = {
        "selected": selected,
        "selected_label": MODEL_LABELS[selected],
        "test_rows": len(test),
        "calibration": calibration(
            valid, predictions[selected]["valid"], test, predictions[selected]["test"]
        ),
        "bootstrap": bootstrap(test, predictions, selected, rounds),
        "fairness": fairness(test, predictions[selected]["test"], rounds),
        "gender": gender_audit(load_dataset()),
        "production": assess(
            test,
            predictions[selected]["test"],
            interval_ratios(valid["salary"].to_numpy(), predictions[selected]["valid"], 0.8),
            rounds,
        ),
        "latest_batch": latest_batch(parts, predictions[selected]),
    }
    path = output or Path(directory or artifacts_dir()) / "validation.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def load_validation():
    path = artifacts_dir() / "validation.json"
    if not path.exists():
        return validate()
    return json.loads(path.read_text(encoding="utf-8"))
