"""Cổng thay model khi huấn luyện lại (spec #87, ticket #90).

Huấn luyện lại ghi vào một thư mục ứng viên, chạy validation trên ứng viên, rồi mới quyết
định có thay model đang phục vụ hay không. Quy tắc chọn mô hình theo valid MAE (ADR 0008)
không đổi: cổng chỉ quyết định thay hay giữ, không dùng test để chọn siêu tham số.
"""

import json
import shutil
from pathlib import Path

from .production_standard import THRESHOLDS

# Độ phủ chỉ "tệ hơn" khi ra ngoài khoảng chuẩn hoặc bị đẩy xa thêm khỏi khoảng đó; trong khoảng
# 75–85% thì mọi giá trị đều chấp nhận được (chủ dự án chốt ngày 06/11/2026, #81).
COVERAGE_BAND = THRESHOLDS["overall"]["coverage_pct"]


def _outside(coverage):
    low, high = COVERAGE_BAND
    return max(low - coverage, coverage - high, 0.0)


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
    if _outside(new["coverage_pct"]) > _outside(now["coverage_pct"]):
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
    if new > now:
        return True, (
            f"Cả hai chưa đạt chuẩn; ứng viên không tệ hơn chỉ số chung nào và qua {new} phạm vi "
            f"so với {now}."
        )
    better = _better_metrics(current, candidate)
    if new == now and better:
        return True, (
            f"Cả hai chưa đạt chuẩn và cùng qua {new} phạm vi; ứng viên tốt hơn ở "
            + ", ".join(better)
            + " và không tệ hơn chỉ số chung nào."
        )
    return False, (
        f"Cả hai chưa đạt chuẩn và ứng viên không tốt hơn: {new} phạm vi so với {now}, "
        "không chỉ số chung nào tốt hơn."
    )


def _better_metrics(current, candidate):
    """Chỉ số chung ứng viên tốt hơn hẳn (bằng số phạm vi vẫn được thay, chốt ở #81)."""
    now, new = _points(current), _points(candidate)
    better = []
    if new["median_error_pct"] < now["median_error_pct"]:
        better.append("median_error_pct")
    if new["within_20_pct"] > now["within_20_pct"]:
        better.append("within_20_pct")
    if _outside(new["coverage_pct"]) < _outside(now["coverage_pct"]):
        better.append("coverage_pct")
    return better


def _promote(candidate, serving):
    serving.mkdir(parents=True, exist_ok=True)
    for path in candidate.iterdir():
        if path.is_file() and path.name != "serving_rescored_validation.json":
            shutil.copy2(path, serving / path.name)


def retrain(serving, candidate, *, train, validate, rescore=None):
    """Huấn luyện vào ``candidate``, kiểm chuẩn, chỉ chép sang ``serving`` khi qua cổng.

    ``rescore(serving, output)`` chấm lại model đang phục vụ trên dữ liệu hiện tại (cùng tập
    test với ứng viên) và ghi ra ``output``; nhờ vậy hai bên được so trên cùng tập test kể cả
    khi bộ dữ liệu đã đổi (#81). Không truyền thì dùng bản chấm đã lưu của model đang phục vụ.
    """
    serving, candidate = Path(serving), Path(candidate)
    if candidate.exists():
        shutil.rmtree(candidate)
    train(candidate)
    validate(candidate)
    current = _production(serving)
    rescored = current is not None and rescore is not None
    if rescored:
        output = candidate / "serving_rescored_validation.json"
        rescore(serving, output)
        current = json.loads(output.read_text(encoding="utf-8")).get("production")
    promoted, reason = decide(current, _production(candidate))
    if promoted:
        _promote(candidate, serving)
    return {
        "promoted": promoted,
        "reason": reason,
        "serving_rescored": rescored,
        "serving": str(serving),
        "candidate": str(candidate),
    }
