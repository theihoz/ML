"""Lô tin tuyển dụng do người quản trị gửi vào (CSV) hoặc do crawler sinh ra (#105).

Một lô hợp lệ được lưu bất biến cùng manifest (nguồn, thời điểm, hash, số dòng) theo nguyên
tắc của ``downloader``: không bao giờ ghi đè bản đã lưu, lô trùng hash thì bỏ qua.
"""

import hashlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .training_labels import data_root

BATCH_COLUMNS = [
    "source",
    "title",
    "company",
    "location",
    "salary_text",
    "experience_text",
    "description",
    "url",
    "posted_date",
]
REQUIRED = ["title", "company", "salary_text"]


class BatchError(ValueError):
    """File lô không đọc được hoặc thiếu cột: cả file bị từ chối."""


def batches_dir():
    return data_root() / "batches"


def validate_batch(frame, source=None):
    """Tách dòng hợp lệ và báo cáo lỗi theo dòng (số dòng tính như trong file, có tiêu đề).

    ``source`` (nếu có) ghi đè cột ``source`` của file; file không có cột này thì bắt buộc.
    """
    frame = frame.copy()
    if source:
        frame["source"] = source
    missing = [column for column in BATCH_COLUMNS if column not in frame.columns]
    if missing:
        raise BatchError(f"Thiếu cột: {', '.join(missing)}")
    frame = frame[BATCH_COLUMNS].fillna("").astype(str).apply(lambda column: column.str.strip())
    errors = []
    keep = []
    for position, row in enumerate(frame.itertuples(index=False)):
        reasons = [f"thiếu {name}" for name in ["source", *REQUIRED] if not getattr(row, name)]
        if row.posted_date and pd.isna(pd.to_datetime(row.posted_date, errors="coerce")):
            reasons.append(f"posted_date không đọc được: {row.posted_date!r}")
        if reasons:
            errors.append({"line": position + 2, "reasons": reasons})
        else:
            keep.append(position)
    return frame.iloc[keep].reset_index(drop=True), errors


def _slug(text):
    return re.sub(r"[^\w]+", "-", text.lower()).strip("-")[:40] or "lo"


def _digest(frame):
    return hashlib.sha256(frame.to_csv(index=False).encode()).hexdigest()


def stored_batches(directory=None):
    """Manifest của mọi lô đã lưu, theo thứ tự nhập."""
    root = Path(directory) if directory else batches_dir()
    manifests = [json.loads(path.read_text()) for path in root.glob("*/manifest.json")]
    return sorted(manifests, key=lambda manifest: (manifest["imported_at"], manifest["id"]))


def load_batch(manifest, directory=None):
    root = Path(directory) if directory else batches_dir()
    frame = pd.read_csv(root / manifest["id"] / "batch.csv", dtype=str, keep_default_na=False)
    if _digest(frame) != manifest["sha256"]:
        raise BatchError(f"Lô {manifest['id']} không khớp hash trong manifest")
    return frame


def save_batch(frame, origin, directory=None, now=None):
    """Lưu một lô đã kiểm tra; lô trùng hash với lô đã có thì không lưu lại."""
    root = Path(directory) if directory else batches_dir()
    digest = _digest(frame)
    for manifest in stored_batches(root):
        if manifest["sha256"] == digest:
            return {"status": "duplicate", "batch": manifest}
    now = now or datetime.now(timezone.utc)
    sources = sorted(set(frame["source"]))
    batch_id = f"{now:%Y%m%dT%H%M%S}-{_slug(sources[0] if sources else 'lo')}-{digest[:8]}"
    target = root / batch_id
    target.mkdir(parents=True, exist_ok=False)
    (target / "batch.csv").write_text(frame.to_csv(index=False), encoding="utf-8")
    manifest = {
        "id": batch_id,
        "sources": sources,
        "origin": origin,
        "imported_at": now.isoformat(timespec="seconds"),
        "rows": len(frame),
        "sha256": digest,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"status": "imported", "batch": manifest}


def import_batch(csv_path, source=None, directory=None, now=None):
    """Đọc CSV theo schema lô tin, lưu dòng hợp lệ và trả về báo cáo (kể cả dòng lỗi)."""
    path = Path(csv_path)
    try:
        text = path.read_text(encoding="utf-8-sig")
        frame = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    except (OSError, UnicodeDecodeError, pd.errors.ParserError) as error:
        raise BatchError(f"Không đọc được {path}: {error}") from error
    valid, errors = validate_batch(frame, source)
    report = {"file": str(path), "rows": len(frame), "accepted": len(valid), "errors": errors}
    if valid.empty:
        return {**report, "status": "rejected"}
    saved = save_batch(
        valid, origin={"type": "csv", "file": path.name}, directory=directory, now=now
    )
    return {**report, **saved}
