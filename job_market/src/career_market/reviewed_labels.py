"""Import only curated, byte-pinned review ledgers, without changing raw sources."""

import csv
import hashlib
import html
import io
import json
import math
import re
from pathlib import Path

from .preparation import digest, review_reasons

APPROVED_MANIFESTS = {
    # User-adjudicated two YODY records; unknown basis and income scope stay separate.
    "afee8f7846cf179a71df05925e034523b7ac337101ad887f00e1e23846eadc5e": "2026-10-29",
}


def _text(raw, transformation):
    if transformation == "raw":
        return raw
    if transformation == "strip_html_unescape_collapse_whitespace_v1":
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", raw))).strip()
    raise ValueError("Phép biến đổi chứng cứ chưa được duyệt.")


def _ledger(directory):
    content = (directory / "manifest.json").read_bytes()
    manifest_hash = hashlib.sha256(content).hexdigest()
    if manifest_hash not in APPROVED_MANIFESTS:
        raise ValueError("Manifest nhãn chưa được duyệt hoặc đã thay đổi SHA-256.")
    manifest = json.loads(content)
    files = {}
    for name, expected in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("Tên file chứng cứ không hợp lệ.")
        data = (directory / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected["sha256"] or len(data) != expected["bytes"]:
            raise ValueError(f"SHA-256/bytes ledger không khớp: {name}")
        files[name] = data
    labels = list(csv.DictReader(io.StringIO(files["accepted_labels.csv"].decode("utf-8"))))
    if len(labels) != manifest["accepted_labels"]:
        raise ValueError("Số nhãn không khớp manifest đã duyệt.")
    return labels, manifest_hash


def apply_reviewed_labels(service, report, directory, *, required=False):
    directory = Path(directory)
    if not directory.is_dir():
        if required:
            raise ValueError("Không tìm thấy thư mục ledger nhãn đã duyệt.")
        labels, manifest_hash = [], None
    else:
        labels, manifest_hash = _ledger(directory)
    selected_sources = {source["source_id"]: source for source in report["sources"]}
    previews = {}
    patches = {}
    for label in labels:
        if label["source_id"] not in selected_sources:
            continue
        if label["decision"] != "accepted":
            raise ValueError("Ledger chứa nhãn chưa được chấp nhận.")
        source = selected_sources[label["source_id"]]
        if (
            label["source_raw_sha256"] != source["raw_sha256"]
            or int(label["source_revision"]) != source["revision"]
        ):
            raise ValueError("Nguồn/revision/SHA-256 nhãn không khớp catalog.")
        if label["source_id"] not in previews:
            previews[label["source_id"]] = service.preview(label["source_id"], limit=None)
        records = previews[label["source_id"]].records
        ordinal = int(label["source_row"])
        if not 1 <= ordinal <= len(records):
            raise ValueError("Record nhãn nằm ngoài nguồn.")
        record = records[ordinal - 1]
        if (
            record.job_id != label["job_id"]
            or record.job_url != label["job_url"]
            or digest(record.raw) != label["source_row_sha256"]
        ):
            raise ValueError("ID/URL/row hash của nhãn không khớp raw.")
        candidates = [row for row in report["eda"] if row["posting_id"] == label["posting_id"]]
        if (
            len(candidates) != 1
            or candidates[0]["role"] != label["role"]
            or candidates[0]["entity_conflicts"]
        ):
            raise ValueError("Nhãn chưa có đúng một tin/nghề EDA được đối chiếu.")
        if label["posting_id"] in patches:
            raise ValueError("Ledger lặp hoặc mâu thuẫn cùng tin.")
        lower, upper, target = (
            float(label[name])
            for name in ("salary_lower", "salary_upper", "salary_target_vnd_month")
        )
        if (
            not all(math.isfinite(v) for v in (lower, upper, target))
            or not 0 < lower <= upper
            or target != (lower + upper) / 2
        ):
            raise ValueError("Khoảng/trung điểm nhãn không hợp lệ.")
        if (
            label["salary_currency"],
            label["salary_period"],
            label["salary_basis"],
            label["compensation_scope"],
        ) != ("VND", "MONTH", "unknown", "advertised_monthly_income"):
            raise ValueError("Cohort của đợt nhãn này chưa được duyệt.")
        salary = service.normalize_salary(record.raw["salary"])
        if (salary["salary_lower"], salary["salary_upper"], salary["salary_currency"]) != (
            lower,
            upper,
            "VND",
        ):
            raise ValueError("Khoảng/currency nhãn không khớp trường salary.")
        if (
            salary["salary_period"] not in {None, "MONTH"}
            or salary["salary_basis"] != label["salary_basis"]
        ):
            raise ValueError("Không được ghi đè kỳ/basis đã được nguồn nêu rõ.")
        evidence = json.loads(label["evidence"])
        monthly = False
        for entry in evidence:
            raw = record.raw.get(entry["field"])
            if (
                raw is None
                or not entry["text"]
                or entry["text"] not in _text(raw, entry["transform"])
            ):
                raise ValueError("Chứng cứ không thuộc đúng trường raw của tin.")
            parsed = service.normalize_salary(entry["text"])
            if parsed["salary_period"] == "MONTH":
                if (parsed["salary_lower"], parsed["salary_upper"]) != (lower, upper) or parsed[
                    "salary_currency"
                ] not in {None, "VND"}:
                    raise ValueError("Chứng cứ kỳ tháng mâu thuẫn khoảng/currency.")
                monthly = True
        if not monthly:
            raise ValueError("Thiếu chứng cứ kỳ tháng cho đúng khoản thu nhập.")
        patches[label["posting_id"]] = {
            "salary_lower": lower,
            "salary_upper": upper,
            "salary_midpoint": target,
            "salary_currency": "VND",
            "salary_period": "MONTH",
            "salary_basis": label["salary_basis"],
            "salary_target_vnd_month": target,
            "salary_status": "valid",
            "salary_reason": "reviewed_same_posting_evidence",
            "compensation_scope": label["compensation_scope"],
            "salary_label_origin": "reviewed_ledger",
            "salary_label_review_id": label["review_id"],
            "salary_label_evidence": {
                "source_row": ordinal,
                "source_row_sha256": label["source_row_sha256"],
                "manifest_sha256": manifest_hash,
                "evidence": evidence,
            },
        }
    # All checks finish before any result is enriched; raw dictionaries stay unchanged.
    for row in report["rows"] + report["eda"]:
        row.update(
            compensation_scope="advertised_salary_unspecified_components",
            salary_label_origin="raw_salary",
            salary_label_review_id=None,
            salary_label_evidence={},
        )
        if row["posting_id"] in patches:
            row.update(patches[row["posting_id"]])
            row["review_reasons"] = review_reasons(row)
    report["targets"] = [row for row in report["eda"] if row["salary_target_vnd_month"] is not None]
    report["summary"]["salary_targets"] = len(report["targets"])
    report["review"] = [row for row in report["rows"] if row["review_reasons"]]
    report["reviewed_labels"] = {
        "manifest_sha256": manifest_hash,
        "accepted_in_ledger": len(labels),
        "imported_postings": len(patches),
        "status": "imported" if manifest_hash else "not_available",
        "training_ready": False,
        "blockers": ["gate_42_open", "support_policy_and_company_split_not_locked"],
    }
    return report
