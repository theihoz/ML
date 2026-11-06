"""Hàng đợi duyệt tay và sổ nhãn đã duyệt (#106, #107).

Mục này làm gì: tin của lô mới mà bộ gắn nhãn tự động không xử lý được (lương thoả thuận,
lương bất thường, không phân loại được vai trò) được ghi vào hàng đợi kèm lý do. Người duyệt
ghi quyết định vào sổ nhãn; lần dựng dữ liệu sau áp dụng sổ này trước khi chia tập.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..paths import data_root
from .rules import LEVELS, ROLE_ORDER, SKILLS

LEDGER_COLUMNS = [
    "key",
    "decision",  # accept | reject
    "salary_min",
    "salary_max",
    "role",
    "level",
    "skills",  # ngăn bằng |, trống = giữ nhãn tự động
    "reviewer",
    "reviewed_at",
    "note",
]
QUEUE_COLUMNS = ["key", "batch", "source", "title", "company", "salary_text", "reason", "url"]


def ledger_path():
    """Đường dẫn sổ nhãn đã duyệt (datasets/labels/reviewed.csv)."""
    return data_root() / "labels" / "reviewed.csv"


def queue_path():
    """Đường dẫn hàng đợi duyệt tay (datasets/processed/review_queue.csv)."""
    return data_root() / "processed" / "review_queue.csv"


def review_key(url, title, company):
    """Khóa ổn định của một tin: URL nếu có, nếu không thì chức danh + công ty đã chuẩn hóa."""
    url = str(url or "").strip()
    if url:
        return url
    normalize = lambda text: re.sub(r"[^\w]", "", str(text or "").lower())  # noqa: E731
    return f"{normalize(title)}|{normalize(company)}"


def load_ledger(path=None):
    """Sổ nhãn đã duyệt dạng {key: dict}; dòng sau ghi đè dòng trước cùng khóa."""
    path = Path(path) if path else ledger_path()
    if not path.exists():
        return {}
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = set(LEDGER_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Sổ nhãn thiếu cột: {', '.join(sorted(missing))}")
    if not frame["decision"].isin(["accept", "reject"]).all():
        raise ValueError("decision phải là accept hoặc reject.")
    for line, row in enumerate(frame.to_dict("records"), 2):
        _check_labels(row, f"Sổ nhãn dòng {line}")
    return {row["key"]: row for row in frame.to_dict("records")}


def _check_labels(row, where):
    """Nhãn ghi tay phải thuộc từ vựng của bộ gắn nhãn, để lỗi gõ không lọt vào dữ liệu."""
    if row.get("role") and row["role"] not in ROLE_ORDER:
        raise ValueError(f"{where}: vai trò không hợp lệ {row['role']!r}")
    if row.get("level") and row["level"] not in LEVELS:
        raise ValueError(f"{where}: cấp bậc không hợp lệ {row['level']!r}")
    unknown = [s for s in str(row.get("skills") or "").split("|") if s and s not in SKILLS]
    if unknown:
        raise ValueError(f"{where}: kỹ năng không hợp lệ {unknown}")


def record_review(key, decision, path=None, reviewer="", note="", **labels):
    """Ghi một quyết định duyệt tay vào sổ (nối thêm, không xóa lịch sử)."""
    if decision not in {"accept", "reject"}:
        raise ValueError("decision phải là accept hoặc reject.")
    unknown = set(labels) - set(LEDGER_COLUMNS)
    if unknown:
        raise ValueError(f"Nhãn không hỗ trợ: {', '.join(sorted(unknown))}")
    path = Path(path) if path else ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {column: "" for column in LEDGER_COLUMNS}
    row.update({k: "" if v is None else str(v) for k, v in labels.items()})
    _check_labels(row, "Nhãn duyệt tay")
    row.update(
        key=key,
        decision=decision,
        reviewer=reviewer,
        note=note,
        reviewed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    frame = pd.DataFrame([row], columns=LEDGER_COLUMNS)
    frame.to_csv(path, mode="a", header=not path.exists(), index=False)
    return row


def ledger_salary(entry):
    """(thấp, cao, trung điểm) từ sổ nếu người duyệt điền lương, nếu không None."""
    try:
        low, high = float(entry["salary_min"]), float(entry["salary_max"])
    except (TypeError, ValueError):
        return None
    if not 0 < low <= high:
        raise ValueError(f"Lương duyệt tay không hợp lệ cho {entry['key']}")
    return round(low, 3), round(high, 3), round((low + high) / 2, 3)


def salary_reason(text):
    """Giải thích bằng lời vì sao không đọc được lương của một tin."""
    raw = str(text or "").lower()
    if re.search(r"thỏa thuận|thoả thuận|thương lượng|cạnh tranh|negotiable", raw):
        return "lương thoả thuận"
    if not re.search(r"\d", raw):
        return "không ghi lương"
    return "lương bất thường hoặc không đọc được"


def load_queue(path=None):
    """Đọc hàng đợi duyệt tay (bảng rỗng nếu chưa có)."""
    path = Path(path) if path else queue_path()
    if not path.exists():
        return pd.DataFrame(columns=QUEUE_COLUMNS)
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def audit_error_rates(review):
    """Tỉ lệ sai của bộ gắn nhãn tự động trên mẫu kiểm tra đã duyệt, theo loại nhãn (#107)."""
    from .label_review import score_review

    scores = score_review(review)
    rows = []
    for field, label in [
        ("salary", "Nhãn lương"),
        ("role", "Vai trò"),
        ("level", "Cấp bậc"),
        ("experience", "Kinh nghiệm"),
    ]:
        score = scores[field]
        rate = 100 - score["accuracy_pct"] if score["accuracy_pct"] is not None else None
        rows.append({"Nhãn": label, "Số tin chấm": score["reviewed"], "Tỉ lệ sai %": rate})
    skills = scores["skills"]
    rate = 100 - skills["precision_pct"] if skills["precision_pct"] is not None else None
    rows.append(
        {
            "Nhãn": "Kỹ năng (mỗi kỹ năng gán)",
            "Số tin chấm": skills["assigned"],
            "Tỉ lệ sai %": rate,
        }
    )
    return pd.DataFrame(rows)
