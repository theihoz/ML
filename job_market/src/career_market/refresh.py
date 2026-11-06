"""Lệnh refresh: chạy cả chuỗi huấn luyện lại (#109).

Mục này làm gì: nhập lô CSV (hoặc tin crawl) → dựng bộ dữ liệu → huấn luyện thành phiên bản
mới → kiểm định → cổng thay model. Bước nào lỗi thì dừng, model đang phục vụ giữ nguyên.
Mỗi bước nhận hàm từ ngoài vào để test chạy trên thư mục tạm.
"""

from .data.batches import BatchError, import_batch, save_batch, stored_batches
from .paths import current_version

MAX_MISSING_SHARE = 0.30
REQUIRED_CRAWL_FIELDS = ("title", "salary_text", "company")


class RefreshStopped(RuntimeError):
    """Một bước của chuỗi refresh thất bại; model đang phục vụ không đổi."""


def check_crawl_output(frame):
    """Dừng khi crawl ra 0 tin hoặc > 30% tin thiếu tiêu đề/lương/công ty (trang đổi giao diện)."""
    if frame is None or len(frame) == 0:
        raise RefreshStopped("Crawl ra 0 tin: dừng trước bước dựng dữ liệu.")
    blank = frame[list(REQUIRED_CRAWL_FIELDS)].fillna("").astype(str).apply(lambda c: c.str.strip())
    share = float((blank == "").any(axis=1).mean())
    if share > MAX_MISSING_SHARE:
        raise RefreshStopped(
            f"{share:.0%} tin crawl thiếu tiêu đề/lương/công ty (> {MAX_MISSING_SHARE:.0%}): "
            "có thể trang đã đổi giao diện, dừng trước bước dựng dữ liệu."
        )
    return share


def refresh(
    csv_files=(),
    source=None,
    crawler=None,
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
        if crawler is not None:
            frame = crawler()
            share = check_crawl_output(frame)
            saved = save_batch(frame, origin={"type": "crawl"}, directory=batches_dir)
            imported.append({"status": saved["status"], "accepted": len(frame), "rows": len(frame)})
            log(f"Crawl: {len(frame)} tin, {share:.0%} thiếu trường bắt buộc, {saved['status']}")
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
