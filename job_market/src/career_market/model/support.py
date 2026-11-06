"""Mức hỗ trợ dữ liệu của một hồ sơ và khoảng lương mở rộng (spec #87, ticket #89).

Giống LinkedIn Salary và Glassdoor: con số lương chỉ hiện khi đủ dữ liệu. Hồ sơ thuộc nhóm
vai trò × cấp bậc có quá ít tin train, hoặc thuộc vai trò/cấp bậc trượt chuẩn production,
chỉ nhận một khoảng lương mở rộng cho đủ độ phủ, kèm lý do.
"""

import numpy as np

from .production import THRESHOLDS

GROUP_COLUMNS = ("role", "level")
GROUP_LABELS = {"role": "Vai trò", "level": "Cấp bậc"}


def _band(salaries, ratios):
    """Hệ số p10/p90 trên valid nếu đủ tin; nếu không, p10–p90 lương thị trường trên train."""
    if len(ratios) >= THRESHOLDS["min_test_rows"]:
        return {
            "kind": "ratio",
            "p10": float(np.quantile(ratios, 0.10)),
            "p90": float(np.quantile(ratios, 0.90)),
            "n_valid": int(len(ratios)),
        }
    return {
        "kind": "market",
        "low": float(np.quantile(salaries, 0.10)),
        "high": float(np.quantile(salaries, 0.90)),
        "n_train": int(len(salaries)),
    }


def build_support(train, valid, valid_predicted):
    """Bảng lưu cùng artifact: số tin train theo nhóm vai trò × cấp bậc và khoảng mở rộng."""
    ratio = valid["salary"].to_numpy() / np.asarray(valid_predicted, dtype=float)
    cohorts = train.groupby(["role", "level"]).size()
    bands = {}
    for column in GROUP_COLUMNS:
        bands[column] = {}
        for group in sorted(set(train[column]) | set(valid[column])):
            in_train = train.loc[train[column] == group, "salary"].to_numpy()
            if not len(in_train):
                in_train = train["salary"].to_numpy()
            bands[column][str(group)] = _band(in_train, ratio[(valid[column] == group).to_numpy()])
    return {
        "cohort_train_rows": {f"{role}|{level}": int(n) for (role, level), n in cohorts.items()},
        "bands": bands,
        "market": _band(train["salary"].to_numpy(), []),
    }


def _apply(band, value):
    if band["kind"] == "ratio":
        return value * band["p10"], value * band["p90"]
    return band["low"], band["high"]


def resolve(role, level, value, report, production):
    """Trạng thái hỗ trợ và khoảng lương cho dự đoán ``value`` của một hồ sơ."""
    support = report["support"]
    failing = (production or {}).get("failing", {})
    reasons = []
    rows = support["cohort_train_rows"].get(f"{role}|{level}", 0)
    minimum = THRESHOLDS["min_train_rows"]
    if rows < minimum:
        reasons.append(f"Nhóm {role} × {level} chỉ có {rows} tin train (cần ≥ {minimum}).")
    groups = {"role": role, "level": level}
    messages = []
    if rows < minimum:
        messages.append(
            f"Có ít tin tuyển dụng công bố lương cho {role} ở cấp {level} ({rows} tin), "
            "nên chỉ hiện khoảng lương."
        )
    for column in GROUP_COLUMNS:
        if groups[column] in failing.get(column, []):
            reasons.append(f"{GROUP_LABELS[column]} {groups[column]} chưa đạt chuẩn production.")
            messages.append(
                f"Dự đoán cho {GROUP_LABELS[column].lower()} {groups[column]} chưa đủ chính xác, "
                "nên chỉ hiện khoảng lương."
            )
    if not reasons:
        band = report["interval_ratio"]
        return {
            "supported": True,
            "support_reasons": [],
            "support_message": "",
            "cohort_rows": rows,
            "salary": value,
            "low": value * band["p10"],
            "high": value * band["p90"],
        }
    ranges = [
        _apply(support["bands"][column].get(str(groups[column]), support["market"]), value)
        for column in GROUP_COLUMNS
    ]
    return {
        "supported": False,
        "support_reasons": reasons,
        # Câu cho người dùng: không dùng thuật ngữ kỹ thuật; chi tiết nằm ở support_reasons.
        "support_message": messages[0],
        "cohort_rows": rows,
        "salary": None,
        "low": min(low for low, _ in ranges),
        "high": max(high for _, high in ranges),
    }
