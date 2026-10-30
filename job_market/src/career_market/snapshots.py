"""Deterministic CSV snapshots with source revisions and content checksums."""

import csv
import hashlib
import io
import json
from pathlib import Path

from .preparation import digest


def csv_bytes(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: json.dumps(row.get(key), ensure_ascii=False, sort_keys=True)
                if isinstance(row.get(key), (dict, list))
                else row.get(key)
                for key in fields
            }
        )
    return stream.getvalue().encode("utf-8")


def snapshot(report, output_dir=None):
    fields = list(report["rows"][0]) if report["rows"] else ["row_id", "salary_target_vnd_month"]
    groups = {
        "rows": report["rows"],
        "eda": report["eda"],
        "salary_targets": report["targets"],
        "review": report["review"],
        "duplicates": report["duplicates"],
    }
    files = {f"{name}.csv": csv_bytes(rows, fields) for name, rows in groups.items()}
    files["repost_groups.json"] = json.dumps(
        report["repost_groups"], ensure_ascii=False, sort_keys=True
    ).encode()
    manifest = {
        "rules_version": report["rules_version"],
        "sources": json.loads(json.dumps(report.get("sources", []))),
        "summary": report["summary"],
        "ml_state": report["ml_state"],
        "reviewed_labels": report.get("reviewed_labels", {}),
        "salary_gate": "https://github.com/theihoz/ML/issues/42",
        "counts_note": "Các partition raw đối chiếu rời nhau; review và salary_targets là tập con, không cộng vào raw.",
        "repost_note": "Nhóm giống trường quan sát để rà soát và chia tập sau này; không tự loại URL khác như cùng một tin. EDA hợp nhất bằng chứng tương thích theo posting_id, truy về rows qua evidence_row_ids; tin mâu thuẫn được cách ly entity_review.",
        "files": {
            name: {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
            for name, content in files.items()
        },
    }
    manifest["snapshot_id"] = digest(manifest)
    files["manifest.json"] = json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, indent=2
    ).encode()
    if output_dir is not None:
        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (destination / name).write_bytes(content)
    return {"report": report, "manifest": manifest, "files": files}
