"""Lệnh refresh: chạy cả chuỗi huấn luyện lại (#109).

Mục này làm gì: nhập lô CSV → dựng bộ dữ liệu → huấn luyện thành phiên bản
mới → kiểm định → cổng thay model. Bước nào lỗi thì dừng, model đang phục vụ giữ nguyên.
Mỗi bước nhận hàm từ ngoài vào để test chạy trên thư mục tạm.
"""

from .data.batches import BatchError, import_batch, stored_batches
from .paths import current_version


class RefreshStopped(RuntimeError):
    """Một bước của chuỗi refresh thất bại; model đang phục vụ không đổi."""


def refresh(
    csv_files=(),
    source=None,
    *,
    build,
    retrain,
    batches_dir=None,
    root=None,
    log=print,
):
    """Chạy cả chuỗi; trả về tóm tắt từng bước. ``retrain`` tạo phiên bản và qua cổng."""
    summary = {"status": "ok", "serving_before": current_version(root)}
    try:
        imported = []
        for path in csv_files:
            try:
                report = import_batch(path, source, directory=batches_dir)
            except BatchError as error:
                raise RefreshStopped(f"Không nhập được {path}: {error}") from error
            if report["status"] == "rejected":
                raise RefreshStopped(f"Lô {path} không có dòng hợp lệ: {report['errors'][:3]}")
            imported.append(report)
            log(
                f"Nhập {path}: {report['accepted']}/{report['rows']} dòng hợp lệ, "
                f"{len(report['errors'])} dòng lỗi, {report['status']}"
            )
        summary["imported"] = imported
        summary["new_rows"] = sum(r["accepted"] for r in imported if r["status"] == "imported")
        summary["duplicate_batches"] = sum(r["status"] == "duplicate" for r in imported)

        dataset = build()
        funnel = dataset["funnel"]
        summary["dataset"] = {
            "rows": dataset["rows"],
            "review_queue": funnel.get("review_queue", 0),
            "duplicates_removed": funnel.get("it_role", 0) - funnel.get("deduplicated", 0),
        }
        log(
            f"Dựng dữ liệu: {dataset['rows']:,} tin, {summary['dataset']['review_queue']} tin vào "
            f"hàng đợi duyệt tay, {summary['dataset']['duplicates_removed']} tin trùng bị loại"
        )

        batches = stored_batches(batches_dir)
        gate = retrain(batches)
        summary["gate"] = gate
        verdict = "thay model" if gate["promoted"] else "giữ model cũ"
        log(f"Cổng thay model: {verdict} ({gate['version']}). Lý do: {gate['reason']}")
    except RefreshStopped as error:
        summary.update(status="stopped", error=str(error))
        log(f"Dừng: {error}")
    summary["serving_after"] = current_version(root)
    return summary
