"""Hiệu chỉnh về lương gross thị trường gần đúng (ADR 0015).

Mục này làm gì: mô hình học từ lương ghi trên tin tuyển dụng. Để ra lương gross người đi
làm thật sự nhận, nhân dự đoán với một hệ số. Hệ số gồm hai phần:
1. theo cấp bậc × thành phố: so trung bình lương TopDev với trung bình dự đoán;
2. theo vai trò: so trung vị ITviec với trung vị dự đoán sau bước 1.
Báo cáo chỉ dùng để tính hệ số, không dùng để huấn luyện mô hình.
"""

import hashlib
import json
from pathlib import Path

import numpy as np

from ..data.reference import load_reference, matching_profiles
from ..paths import artifacts_dir, data_root
from .estimators import CURRENT_YEAR, feature_frame


def _digest(path):
    """Mã băm của file, để phát hiện hệ số được tính cho một mô hình khác."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_calibration(frame, models, report, output):
    """Tính hệ số hiệu chỉnh gross cho từng mô hình và lưu vào calibration.json."""
    reference = load_reference()
    anchors = reference[(reference["purpose"] == "calibration") & (reference["basis"] == "gross")]
    train = frame[frame["split"] == "train"].copy()
    train["year"] = CURRENT_YEAR
    result = {
        "version": 2,
        "inference_year": CURRENT_YEAR,
        "role_anchor_statistic": "equal-edition arithmetic mean of published medians",
        "approximate": True,
        "anchor_statistic": "mean",
        "reference_sha256": _digest(data_root() / "reference" / "salary_reference.csv"),
        "metrics_sha256": _digest(output / "metrics.json"),
        "models": {},
    }
    for name, model in models.items():
        train["prediction"] = (
            model.predict(feature_frame(train)) * report["models"][name]["interval_ratio"]["p50"]
        )
        cells, levels = {}, {}
        for row in anchors.to_dict("records"):
            cohort = matching_profiles(train, row)
            if cohort.empty:
                continue
            # So trung bình với trung bình, không đổi tên mean của nguồn thành median.
            factor = float(row["value"]) / float(cohort["prediction"].mean())
            if not np.isfinite(factor) or factor <= 0:
                raise ValueError("Hệ số hiệu chỉnh phải dương và hữu hạn.")
            for level in row["level"].split("|"):
                cells[f"{level}|{row['region']}"] = factor
                levels.setdefault(level, []).append(factor)
        table = {
            "cells": cells,
            "levels": {level: float(np.median(values)) for level, values in levels.items()},
            "model_sha256": _digest(output / f"{name}.joblib"),
        }
        train["city_prediction"] = train.apply(
            lambda r: r["prediction"] * calibration_for(table, r["level"], r["region"])["factor"],
            axis=1,
        )
        roles = {}
        role_rows = reference[
            (reference["purpose"] == "role_calibration") & (reference["basis"] == "gross")
        ]
        for role, rows in role_rows.groupby("role"):
            cohort = train[train["role"] == role]
            if cohort.empty:
                continue
            anchor = float(rows["value"].astype(float).mean())
            roles[role] = {
                "factor": anchor / float(cohort["city_prediction"].median()),
                "composite_anchor": anchor,
                "source_ids": rows["id"].tolist(),
                "mapping_caveats": sorted(set(rows["mapping_caveat"]) - {""}),
            }
        table["roles"] = roles
        result["models"][name] = table
    (output / "calibration.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def load_calibration(name):
    """Đọc hệ số đã lưu và kiểm tra nó khớp đúng mô hình đang dùng."""
    root = artifacts_dir()
    path = root / "calibration.json"
    if not path.exists():
        raise RuntimeError("Thiếu hệ số hiệu chỉnh calibration.json; hãy huấn luyện lại.")
    result = json.loads(path.read_text())
    for required in (
        root / "metrics.json",
        root / f"{name}.joblib",
        data_root() / "reference" / "salary_reference.csv",
    ):
        if not required.is_file():
            raise RuntimeError(f"Thiếu dữ liệu hiệu chỉnh {required}; hãy khôi phục artifact.")
    if (
        result.get("version") != 2
        or result.get("inference_year") != CURRENT_YEAR
        or name not in result.get("models", {})
        or result["reference_sha256"] != _digest(data_root() / "reference" / "salary_reference.csv")
        or result["metrics_sha256"] != _digest(root / "metrics.json")
        or result["models"][name]["model_sha256"] != _digest(root / f"{name}.joblib")
    ):
        raise RuntimeError("Hệ số hiệu chỉnh không khớp mô hình/bộ đối chiếu; hãy huấn luyện lại.")
    return result["models"][name]


def calibration_for(table, level, region, role=None):
    """Hệ số gross cho một hồ sơ (cấp bậc, khu vực, vai trò) kèm cảnh báo nếu phải dùng dự phòng."""
    key = f"{level}|{region}"
    if key in table["cells"]:
        factor, scope = table["cells"][key], "level_city"
    elif level in table["levels"]:
        factor, scope = table["levels"][level], "level"
    elif level == "Intern" and "Fresher" in table["levels"]:
        # Không có khảo sát Intern: giữ tương quan mô hình, mượn hệ số Fresher.
        factor = table["cells"].get(f"Fresher|{region}", table["levels"]["Fresher"])
        scope = "fresher_proxy"
    else:
        factor, scope = 1.0, "uncalibrated"
    if not np.isfinite(factor) or factor <= 0:
        raise ValueError("Hệ số hiệu chỉnh không hợp lệ.")
    city_factor = factor
    role_anchor = table.get("roles", {}).get(role, {})
    role_factor = role_anchor.get("factor", 1.0)
    if not np.isfinite(role_factor) or role_factor <= 0:
        raise ValueError("Hệ số vai trò phải dương và hữu hạn.")
    warnings = []
    if scope == "fresher_proxy":
        warnings.append("Chưa có mốc khảo sát Intern; mượn hệ số Fresher, chỉ nên tham khảo.")
    elif scope != "level_city":
        warnings.append(f"Hiệu chỉnh cấp bậc/thành phố dùng dự phòng: {scope}.")
    if role is not None and not role_anchor:
        warnings.append("Chưa có mốc gross cho vai trò; hệ số vai trò bằng 1.")
    # "exact" = vai trò khớp đúng nhóm trong báo cáo: không cần cảnh báo. Ghi chú khác (tiếng Anh,
    # dành cho người bảo trì) được thay bằng một câu dễ hiểu cho người dùng; bản gốc vẫn trả về.
    if any(c != "exact" for c in role_anchor.get("mapping_caveats", [])):
        warnings.append(
            "Báo cáo lương không có đúng nhóm vai trò này; hệ số gross dựa trên nhóm gần nhất, "
            "chỉ nên tham khảo."
        )
    return {
        "factor": city_factor * role_factor,
        "city_factor": city_factor,
        "role_factor": role_factor,
        "scope": scope,
        "approximate": True,
        "basis": "gross",
        "anchor_statistic": "mean",
        "role_anchor_statistic": "equal-edition arithmetic mean of published medians",
        "warnings": warnings,
        **{k: v for k, v in role_anchor.items() if k != "factor"},
    }


def calibrate_predictions(frame, predictions, table, include_role=True):
    """Same current-year multiplicative transform used by advise and reality checks."""
    return np.asarray(predictions) * np.array(
        [
            calibration_for(table, row.level, row.region, row.role if include_role else None)[
                "factor"
            ]
            for row in frame.itertuples()
        ]
    )
