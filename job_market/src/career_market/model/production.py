"""Chuẩn production cho dự đoán lương (spec #87, quyết định #78).

Chấm theo cách các sản phẩm dự đoán lương thực tế công bố độ chính xác:
- trung vị sai số % và tỉ lệ dự đoán sai không quá 20% (Glassdoor),
- độ phủ của khoảng p10–p90 hiển thị cho người dùng (LinkedIn Salary).

Ngưỡng chung so bằng cận bất lợi của khoảng tin cậy bootstrap 95%, lấy mẫu lại theo công
ty, để mô hình không qua chuẩn chỉ nhờ may mắn của tập test. Ngưỡng theo nhóm (vai trò, cấp
bậc) so bằng giá trị điểm: với vài chục tin test, khoảng bootstrap của nhóm quá rộng để
quyết định nhóm nào phải ẩn con số lương (điều chỉnh 06/11/2026, ghi ở #87). Khoảng tin
cậy của nhóm vẫn được lưu để tham khảo.
"""

import numpy as np

THRESHOLDS = {
    "overall": {"median_error_pct": 15, "within_20_pct": 65, "coverage_pct": (75, 85)},
    "group": {"median_error_pct": 20, "within_20_pct": 50, "coverage_pct": (70, 100)},
    # Nhóm vai trò/cấp bậc cần ít nhất ngần này tin test để được chấm.
    "min_test_rows": 20,
    # Nhóm vai trò × cấp bậc cần ít nhất ngần này tin train để hiện con số lương.
    "min_train_rows": 20,
    # Mức Glassdoor công bố: mục tiêu dài hạn, không phải điều kiện lên production.
    "long_term": {"median_error_pct": 10, "within_20_pct": 75},
}
METRICS = ("median_error_pct", "within_20_pct", "coverage_pct")
GROUP_COLUMNS = ("role", "level")


def _metric_values(error_pct, inside):
    """Ba chỉ số chuẩn: trung vị sai số %, tỉ lệ sai ≤ 20%, độ phủ khoảng p10–p90."""
    return {
        "median_error_pct": float(np.median(error_pct)),
        "within_20_pct": float((error_pct <= 20).mean() * 100),
        "coverage_pct": float(inside.mean() * 100),
    }


def _company_samples(companies, rounds, seed):
    """Bốc ngẫu nhiên lại các công ty (có thể trùng) cho mỗi lần thi lại bootstrap."""
    rng = np.random.default_rng(seed)
    codes, keys = np.unique(companies, return_inverse=True)
    members = [np.flatnonzero(keys == k) for k in range(len(codes))]
    for _ in range(rounds):
        chosen = rng.integers(0, len(members), len(members))
        yield np.concatenate([members[i] for i in chosen])


def _judge(metric, point, ci95, limits, by_point=False):
    """So với ngưỡng: theo cận bất lợi (sai số dùng cận trên, tỉ lệ đúng dùng cận dưới, độ
    phủ cả hai cận) hoặc theo giá trị điểm khi ``by_point``."""
    limit = limits[metric]
    low, high = (point, point) if by_point else ci95
    if metric == "median_error_pct":
        passed = high <= limit
    elif metric == "within_20_pct":
        passed = low >= limit
    else:
        passed = limit[0] <= low and high <= limit[1]
    return {
        "point": point,
        "ci95": ci95,
        "threshold": limit,
        "judged_on": "point" if by_point else "ci95",
        "pass": bool(passed),
    }


def _score(error_pct, inside, samples, limits, by_point=False):
    """Chấm một nhóm tin theo ba chỉ số và so với ngưỡng."""
    boot = {metric: [] for metric in METRICS}
    for index in samples:
        if len(index):
            for metric, value in _metric_values(error_pct[index], inside[index]).items():
                boot[metric].append(value)
    point = _metric_values(error_pct, inside)
    metrics = {
        metric: _judge(
            metric,
            point[metric],
            [float(np.percentile(boot[metric], 2.5)), float(np.percentile(boot[metric], 97.5))],
            limits,
            by_point,
        )
        for metric in METRICS
    }
    status = "pass" if all(m["pass"] for m in metrics.values()) else "fail"
    return {"n": len(error_pct), "status": status, "metrics": metrics}


def assess(test, predicted, band, rounds=1000, seed=42):
    """Chấm chuẩn production trên tập test.

    ``test`` cần các cột salary, company_key, role, level; ``band`` là hệ số (thấp, cao)
    của khoảng p10–p90 dựng trên tập valid.
    """
    actual = test["salary"].to_numpy(dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    error_pct = np.abs(predicted - actual) / actual * 100
    inside = (actual >= predicted * band[0]) & (actual <= predicted * band[1])
    samples = list(_company_samples(test["company_key"].to_numpy(), rounds, seed))
    result = {
        "thresholds": THRESHOLDS,
        "band": [float(band[0]), float(band[1])],
        "rounds": rounds,
        "overall": _score(error_pct, inside, samples, THRESHOLDS["overall"]),
    }
    minimum = THRESHOLDS["min_test_rows"]
    for column in GROUP_COLUMNS:
        values = test[column].astype(str).to_numpy()
        rows = []
        for group in sorted(set(values)):
            mask = values == group
            if mask.sum() < minimum:
                rows.append({"group": group, "n": int(mask.sum()), "status": "not_scored"})
                continue
            positions = np.flatnonzero(mask)
            remap = np.full(len(values), -1)
            remap[positions] = np.arange(len(positions))
            group_samples = [remap[index[mask[index]]] for index in samples]
            scored = _score(
                error_pct[mask], inside[mask], group_samples, THRESHOLDS["group"], by_point=True
            )
            rows.append({"group": group, **scored})
        result[column] = sorted(rows, key=lambda row: -row["n"])
    result["failing"] = {
        column: [row["group"] for row in result[column] if row["status"] == "fail"]
        for column in GROUP_COLUMNS
    }
    result["production_ready"] = result["overall"]["status"] == "pass" and not any(
        result["failing"].values()
    )
    long_term = THRESHOLDS["long_term"]
    overall = result["overall"]["metrics"]
    result["long_term"] = {
        "median_error_pct": overall["median_error_pct"]["ci95"][1] <= long_term["median_error_pct"],
        "within_20_pct": overall["within_20_pct"]["ci95"][0] >= long_term["within_20_pct"],
    }
    return result
