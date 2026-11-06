"""Kiểm tra thực tế: so dự đoán với báo cáo lương bên ngoài (#115).

Mục này làm gì: với mỗi vai trò trong báo cáo TopDev, lấy trung vị lương dự đoán (đã quy về
gross) và so với trung vị báo cáo; đạt khi lệch không quá 15% ở ít nhất 80% vai trò. Các
mốc đã dùng để tính hệ số hiệu chỉnh được báo riêng, không tính là bằng chứng độc lập.
"""

from ..data.dataset import load_dataset
from ..data.reference import load_reference, matching_profiles
from .calibration import calibrate_predictions, load_calibration
from .estimators import CURRENT_YEAR, feature_frame
from .training import load_model


def _summary(cells, tolerance, required):
    """Tổng hợp các ô đã chấm thành kết luận đạt / không đạt / chưa có dữ liệu."""
    scored = [row for row in cells if row["relative_error"] is not None]
    rate = sum(row["passed"] for row in scored) / len(cells) if cells else None
    return {
        "status": "đạt"
        if rate is not None and rate >= required
        else "chưa có dữ liệu"
        if not cells
        else "không đạt",
        "passed": rate >= required if rate is not None else None,
        "total": len(cells),
        "scored": len(scored),
        "pass_rate": rate,
        "tolerance": tolerance,
        "required_rate": required,
        "cells": cells,
    }


def reality_check(reference_path=None, model_name=None):
    """So mô hình với báo cáo lương bên ngoài; trả kết quả từng ô."""
    model, name, report = load_model(model_name)
    # Dùng phân bố hồ sơ TRAIN làm trọng số; không coi tin này là số lương khảo sát.
    frame = load_dataset()
    frame = frame[frame["split"] == "train"].copy()
    frame["year"] = CURRENT_YEAR
    band = report["models"][name].get("interval_ratio", report["interval_ratio"])
    frame["predicted"] = model.predict(feature_frame(frame)) * band.get("p50", 1.0)
    table = load_calibration(name)
    frame["before_role"] = calibrate_predictions(
        frame, frame["predicted"], table, include_role=False
    )
    frame["predicted"] = calibrate_predictions(frame, frame["predicted"], table)
    cells, anchors, unknown, role_anchors, context = [], [], [], [], []
    for row in load_reference(reference_path).to_dict("records"):
        cohort = matching_profiles(frame, row)
        value = float(row["value"])
        prediction = (
            float(
                cohort["predicted"].mean()
                if row["statistic"] == "mean"
                else cohort["predicted"].median()
            )
            if len(cohort)
            else None
        )
        error = abs(prediction - value) / value if prediction is not None else None
        cell = {
            **row,
            "prediction": prediction,
            "before_role_prediction": float(
                cohort["before_role"].mean()
                if row["statistic"] == "mean"
                else cohort["before_role"].median()
            )
            if len(cohort)
            else None,
            "profile_count": len(cohort),
            "relative_error": error,
            "passed": error <= 0.15 if error is not None else False,
        }
        if row["purpose"] == "calibration":
            anchors.append(cell)
        elif row["basis"] != "gross":
            unknown.append(cell)
        elif row["purpose"] == "evaluation" and row["statistic"] == "median":
            cells.append(cell)
        elif row["purpose"] == "role_calibration":
            role_anchors.append(cell)
        else:
            context.append(cell)
    return {
        "model": name,
        "reference": _summary(cells, 0.15, 0.8),
        "calibration_cells": anchors,
        "unknown_basis_cells": unknown,
        "role_calibration_cells": role_anchors,
        "context_cells": context,
        "inference_year": CURRENT_YEAR,
        "prediction_basis": "gross market; approximate two-stage calibration",
        "limitations": [
            "Ô theo vai trò là toàn quốc; chưa xác nhận riêng HN/HCM.",
            "Trọng số hồ sơ lấy từ train, khác phân bố người trả lời khảo sát.",
            "Mốc city/level là mean; mốc vai trò là trung bình hai median ITviec, không phải pooled median.",
            "Không fit lại city sau vai trò: trung bình city cuối có thể lệch mốc ban đầu.",
            "Phân vị khoảng dựa trên độ phân tán lương chào tuyển valid, không phải phân vị khảo sát gross.",
            "Hồ sơ được dự đoán ở năm 2026 như form; chưa quy đổi thời giá báo cáo 2024/2025.",
            "TopDev kết hợp JD và khảo sát; chưa phải kiểm chứng thu nhập thuần túy.",
        ],
    }
