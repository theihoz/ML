"""Cổng thay model khi huấn luyện lại (spec #87, ticket #90).

Huấn luyện lại ghi vào một thư mục ứng viên, chạy validation trên ứng viên, rồi mới quyết
định có thay model đang phục vụ hay không. Quy tắc chọn mô hình theo valid MAE (ADR 0008)
không đổi: cổng chỉ quyết định thay hay giữ, không dùng test để chọn siêu tham số.
"""

import json
import shutil
from pathlib import Path

# Hướng "tốt hơn" của từng chỉ số chung; độ phủ tốt hơn khi gần mức danh nghĩa 80%.
NOMINAL_COVERAGE = 80


def _production(directory):
    path = Path(directory) / "validation.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("production")


def _points(production):
    return {name: m["point"] for name, m in production["overall"]["metrics"].items()}


def _passed_scopes(production):
    groups = [row for column in ("role", "level") for row in production.get(column, [])]
    return (production["overall"]["status"] == "pass") + sum(
        row["status"] == "pass" for row in groups
    )


def _worse_metrics(current, candidate):
    now, new = _points(current), _points(candidate)
    worse = []
    if new["median_error_pct"] > now["median_error_pct"]:
        worse.append("median_error_pct")
    if new["within_20_pct"] < now["within_20_pct"]:
        worse.append("within_20_pct")
    if abs(new["coverage_pct"] - NOMINAL_COVERAGE) > abs(now["coverage_pct"] - NOMINAL_COVERAGE):
        worse.append("coverage_pct")
    return worse


def decide(current, candidate):
    """(thay?, lý do) cho báo cáo chuẩn production của model đang phục vụ và ứng viên."""
    if current is None:
        return True, "Chưa có model đang phục vụ: dùng ứng viên."
    if candidate["production_ready"]:
        return True, "Ứng viên đạt chuẩn production."
    if current["production_ready"]:
        return False, "Ứng viên không đạt chuẩn production, model đang phục vụ đạt: giữ model cũ."
    worse = _worse_metrics(current, candidate)
    if worse:
        return False, (
            "Cả hai chưa đạt chuẩn và ứng viên tệ hơn ở chỉ số chung: " + ", ".join(worse) + "."
        )
    now, new = _passed_scopes(current), _passed_scopes(candidate)
    if new <= now:
        return False, (
            f"Cả hai chưa đạt chuẩn và ứng viên không qua thêm phạm vi nào ({new} so với {now})."
        )
    return True, (
        f"Cả hai chưa đạt chuẩn; ứng viên không tệ hơn chỉ số chung nào và qua {new} phạm vi "
        f"so với {now}."
    )


def _promote(candidate, serving):
    serving.mkdir(parents=True, exist_ok=True)
    for path in candidate.iterdir():
        if path.is_file():
            shutil.copy2(path, serving / path.name)


def retrain(serving, candidate, *, train, validate):
    """Huấn luyện vào ``candidate``, kiểm chuẩn, chỉ chép sang ``serving`` khi qua cổng."""
    serving, candidate = Path(serving), Path(candidate)
    if candidate.exists():
        shutil.rmtree(candidate)
    train(candidate)
    validate(candidate)
    promoted, reason = decide(_production(serving), _production(candidate))
    if promoted:
        _promote(candidate, serving)
    return {
        "promoted": promoted,
        "reason": reason,
        "serving": str(serving),
        "candidate": str(candidate),
    }
