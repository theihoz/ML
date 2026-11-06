"""Phiên bản model và quay lại bản cũ (#108).

Mục này làm gì: mỗi lần huấn luyện lại tạo một thư mục phiên bản trong ``artifacts/``
(model, ảnh chụp dữ liệu đã gắn nhãn, manifest). File ``artifacts/CURRENT`` chỉ phiên bản
đang phục vụ; app và ``load_model`` đọc qua ``paths.artifacts_dir()`` nên đổi con trỏ là
đổi model. Thư mục ``salary-v2`` có sẵn là phiên bản đầu tiên.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ..paths import FIRST_VERSION, artifacts_root, current_version, dataset_path
from .promotion import decide

POINTER = "CURRENT"
HISTORY = "HISTORY.json"
MANIFEST = "manifest.json"


def _history(root):
    """Danh sách các phiên bản đã từng phục vụ, theo thứ tự."""
    path = Path(root) / HISTORY
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else [FIRST_VERSION]


def _point(root, name, history):
    """Ghi con trỏ CURRENT sang phiên bản mới và lưu lịch sử."""
    root = Path(root)
    (root / POINTER).write_text(name + "\n", encoding="utf-8")
    (root / HISTORY).write_text(json.dumps(history, ensure_ascii=False, indent=2), "utf-8")


def _production(directory):
    """Đọc kết quả chấm chuẩn production của một phiên bản."""
    path = Path(directory) / "validation.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("production")


def write_manifest(directory, *, created_at=None, promoted=None, batches=None):
    """Manifest của một phiên bản: dữ liệu, số tin train, trạng thái chuẩn production."""
    directory = Path(directory)
    metrics = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
    summary_path = directory / "dataset.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    production = _production(directory)
    manifest = {
        "version": directory.name,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset_rows": metrics["dataset_rows"],
        "train_rows": metrics["split"]["train"],
        "selected": metrics["selected"],
        "production_ready": bool(production and production["production_ready"]),
        "promoted": promoted,
        "last_import": max((b["imported_at"] for b in batches or []), default=None),
        "batches": [b["id"] for b in batches or []],
        "funnel": summary.get("funnel", {}),
    }
    (directory / MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def read_manifest(directory):
    """Đọc thông tin của một phiên bản (ngày tạo, số tin, trạng thái chuẩn)."""
    path = Path(directory) / MANIFEST
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def current_manifest(root=None):
    """Manifest của phiên bản đang phục vụ (dùng cho dòng độ mới trên app, #111)."""
    root = Path(root) if root else artifacts_root()
    return read_manifest(root / current_version(root))


def list_versions(root=None):
    """Mọi phiên bản, cũ trước mới sau, đánh dấu bản đang phục vụ."""
    root = Path(root) if root else artifacts_root()
    serving = current_version(root)
    rows = []
    for directory in sorted(p for p in root.iterdir() if (p / "metrics.json").exists()):
        manifest = read_manifest(directory) or {"version": directory.name}
        rows.append({**manifest, "current": directory.name == serving})
    return sorted(rows, key=lambda row: (row.get("created_at") or "", row["version"]))


def snapshot_dataset(directory):
    """Chép bộ dữ liệu đã gắn nhãn (CSV + tóm tắt) vào thư mục phiên bản."""
    directory = Path(directory)
    shutil.copy2(dataset_path(), directory / "dataset.csv")
    summary = dataset_path().with_suffix(".json")
    if summary.exists():
        shutil.copy2(summary, directory / "dataset.json")


def retrain_version(*, train, validate, rescore=None, root=None, batches=None, now=None):
    """Huấn luyện vào một phiên bản mới; chỉ chuyển ``CURRENT`` khi qua cổng thay model.

    Phiên bản trượt cổng vẫn được giữ lại để phân tích.
    """
    root = Path(root) if root else artifacts_root()
    now = now or datetime.now(timezone.utc)
    name = f"{FIRST_VERSION}-{now:%Y%m%d-%H%M%S}"
    directory = root / name
    if directory.exists():
        raise FileExistsError(f"Phiên bản {name} đã tồn tại")
    train(directory)
    validate(directory)
    serving_dir = root / current_version(root)
    current = _production(serving_dir)
    rescored = current is not None and rescore is not None
    if rescored:
        output = directory / "serving_rescored_validation.json"
        rescore(serving_dir, output)
        current = json.loads(output.read_text(encoding="utf-8")).get("production")
    promoted, reason = decide(current, _production(directory))
    try:
        snapshot_dataset(directory)
    except FileNotFoundError:
        pass  # thư mục tạm của test có thể không có bộ dữ liệu
    write_manifest(
        directory, created_at=now.isoformat(timespec="seconds"), promoted=promoted, batches=batches
    )
    if promoted:
        _point(root, name, [*_history(root), name])
    return {
        "version": name,
        "promoted": promoted,
        "reason": reason,
        "serving_rescored": rescored,
        "current": current_version(root),
    }


def rollback(root=None):
    """Chuyển ``CURRENT`` về phiên bản đã phục vụ trước đó."""
    root = Path(root) if root else artifacts_root()
    history = _history(root)
    if len(history) < 2:
        raise ValueError("Không có phiên bản nào trước phiên bản đang phục vụ.")
    history = history[:-1]
    _point(root, history[-1], history)
    return {"current": history[-1], "history": history}


def freshness_line(manifest=None):
    """Dòng độ mới cho app (#111): phiên bản, ngày cập nhật, số tin train, trạng thái chuẩn."""
    manifest = manifest or current_manifest()
    if not manifest:
        return "Chưa có thông tin phiên bản dữ liệu."
    updated = (manifest.get("last_import") or manifest.get("created_at") or "")[:10]
    status = "đạt chuẩn production" if manifest.get("production_ready") else "bản thử nghiệm"
    return (
        f"Phiên bản {manifest['version']} · cập nhật {updated} · "
        f"{manifest['train_rows']:,} tin train · {status}"
    )
