"""Prepare traceable EDA records; salary eligibility never initiates training."""

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime

from .postings import posting_key

RULES_VERSION = "eda-v6"


def digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def posting_date(raw):
    text = raw.get("announcement_date", raw.get("date_posted", ""))
    for format in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return text, datetime.strptime(text, format).date().isoformat()
        except ValueError:
            pass
    return text, None


def review_reasons(row):
    reasons = []
    if row["partition"] != "eda":
        reasons.append(row["partition"])
    for domain, valid in (("location", "normalized"), ("experience", "ok"), ("salary", "valid")):
        if row[f"{domain}_status"] != valid:
            reasons.append(f"{domain}: {row[f'{domain}_reason']}")
    if not row["posting_date"]:
        reasons.append("date: chưa có ngày đăng hợp lệ")
    if row["entity_conflicts"]:
        reasons.append("entity: conflicting " + ", ".join(row["entity_conflicts"]))
    return reasons


def reconcile_postings(rows):
    """Combine compatible observations of one identity, keeping every source row."""
    members_by_id = defaultdict(list)
    for row in rows:
        if row["posting_id"]:
            members_by_id[row["posting_id"]].append(row)
    entities = []
    for members in members_by_id.values():
        representative = members[0]
        entity = dict(representative)
        entity["evidence_row_ids"] = [row["row_id"] for row in members]
        for field in ("title_raw", "company_raw"):
            observed = sorted({row[field].strip() for row in members if row[field].strip()})
            entity[field] = observed[0] if observed else ""
        # Classify each observation within its own section boundaries. Joining
        # JDs would let a Requirements heading swallow another row's duties.
        matched = [row for row in members if row["role_status"] == "matched"]
        ambiguous = any(row["role_status"] == "review" and row["role_evidence"] for row in members)
        if len({row["role"] for row in matched}) == 1 and not ambiguous:
            entity.update({key: matched[0][key] for key in ("role", "role_status", "role_reason")})
        elif matched or ambiguous or any(row["role_status"] == "review" for row in members):
            entity.update(
                role=None,
                role_status="review",
                role_reason="Cần review bằng chứng nghề trong các dòng của cùng tin.",
            )
        entity["partition"] = {"matched": "eda", "review": "role_review"}.get(
            entity["role_status"], "out_of_scope"
        )
        representative["partition"] = entity["partition"]
        for prefix in ("salary", "experience"):
            donor = next((row for row in members if row[f"{prefix}_raw"]), representative)
            entity.update(
                {key: value for key, value in donor.items() if key.startswith(prefix + "_")}
            )
        dated = next((row for row in members if row["posting_date"]), representative)
        entity.update({key: dated[key] for key in ("date_raw", "posting_date", "date_kind")})
        for field in ("locations", "skills", "work_modes", "location_unresolved"):
            entity[field] = sorted({value for row in members for value in row[field]})
        for field in ("skill_evidence", "role_evidence", "work_mode_evidence"):
            evidence = {digest(value): value for row in members for value in row[field]}
            entity[field] = [evidence[key] for key in sorted(evidence)]
        entity["location_aliases"] = {
            key: value for row in members for key, value in row["location_aliases"].items()
        }
        entity["has_job_description"] = any(row["has_job_description"] for row in members)
        entity["location_status"] = (
            "review"
            if entity["location_unresolved"]
            else "normalized"
            if entity["locations"] or entity["work_modes"]
            else "missing"
        )
        entity["location_reason"] = (
            "Còn chuỗi địa điểm chưa rõ; xem các dòng bằng chứng của tin."
            if entity["location_unresolved"]
            else "Giữ nhãn địa điểm và hình thức từ các dòng bằng chứng của tin."
        )
        # Different labels/bounds/roles are not complementary evidence. Keep them
        # for review instead of choosing whichever observation happened to be first.
        conflicts = []
        for field in (
            "title_raw",
            "company_raw",
            "role",
            "salary_raw",
            "experience_raw",
            "posting_date",
        ):
            observed = {
                str(row[field]).strip().casefold()
                for row in members
                if row[field] not in (None, "")
            }
            if len(observed) > 1:
                conflicts.append(field)
        entity["entity_conflicts"] = conflicts
        if conflicts:
            entity["partition"] = representative["partition"] = "entity_review"
            reason = "entity: conflicting " + ", ".join(conflicts)
            representative["entity_conflicts"] = conflicts
            representative["review_reasons"].append(reason)
            entity["review_reasons"] = list(representative["review_reasons"])
            entity["salary_target_vnd_month"] = None
        entity["review_reasons"] = review_reasons(entity)
        entity["repost_group_id"] = digest(
            [
                entity["company_raw"].strip().casefold(),
                entity["title_raw"].strip().casefold(),
                entity["locations"],
                sorted({row["raw"].get("job_description", "").strip() for row in members}),
                sorted({row["raw"].get("job_requirements", "").strip() for row in members}),
                entity["experience_raw"],
                entity["salary_raw"],
                sorted(conflicts),
            ]
        )
        for row in members:
            row["repost_group_id"] = entity["repost_group_id"]
        entities.append(entity)
    return entities


def prepare_records(service, records):
    rows, seen = [], {}
    for record in records:
        raw = record.raw
        title = raw.get("job_title", raw.get("title", ""))
        company = raw.get("company_title", raw.get("company", ""))
        description, requirements = raw.get("job_description", ""), raw.get("job_requirements", "")
        date_raw, date = posting_date(raw)
        row = {
            "row_id": f"{record.source_id}:{len(rows) + 1}",
            "source_id": record.source_id,
            "job_id": record.job_id,
            "job_url": record.job_url,
            "title_raw": title,
            "company_raw": company,
            "location_raw": raw.get("location", ""),
            "salary_raw": raw.get("salary", ""),
            "experience_raw": raw.get("exp", raw.get("experience", "")),
            "date_raw": date_raw,
            "posting_date": date,
            "date_kind": "posting",
            "has_job_description": bool(description or requirements),
            "raw": dict(raw),
            **service.classify_role(title, description, requirements),
            **service.normalize_locations(raw.get("location", "")),
            **service.normalize_salary(raw.get("salary", "")),
            **service.normalize_experience(raw.get("exp", raw.get("experience", ""))),
            **service.extract_skills(title, description, requirements),
            "duplicate_of": None,
            "evidence_row_ids": [f"{record.source_id}:{len(rows) + 1}"],
            "entity_conflicts": [],
            "repost_group_id": None,
        }
        row["work_mode_evidence"] = []
        if "Remote" in row["work_modes"]:
            row["work_mode_evidence"].append({"field": "location", "text": row["location_raw"]})
        if re.search(
            r"^remote\b|[\[(]\s*remote\b|\bremote(?=\s*(?:$|[\])]|(?:tại|tai)\b))"
            r"|\b(?:fully|full|100%)\s+remote\b",
            title,
            re.I,
        ) and not re.search(
            r"\b(?:no|not|non)[ -]+remote\b"
            r"|\bremote\s+(?:sensing|procedure\s+call|desktop|access|control|method\s+invocation)\b",
            title,
            re.I,
        ):
            if "Remote" not in row["work_modes"]:
                row["work_modes"].append("Remote")
            row["work_mode_evidence"].append({"field": "title", "text": title})
        try:
            row["posting_id"] = posting_key(record.source_id, record.job_url, record.job_id)
        except ValueError:
            row["posting_id"] = None
        if row["posting_id"] is None:
            row["partition"] = "invalid_identity"
        elif row["posting_id"] in seen:
            row["partition"] = "duplicates"
            row["duplicate_of"] = seen[row["posting_id"]]
        else:
            seen[row["posting_id"]] = row["row_id"]
            row["partition"] = {"matched": "eda", "review": "role_review"}.get(
                row["role_status"], "out_of_scope"
            )
        row["review_reasons"] = review_reasons(row)
        rows.append(row)
    entities = reconcile_postings(rows)
    groups = defaultdict(list)
    for row in rows:
        if row["posting_id"]:
            groups[row["repost_group_id"]].append(row)
    counts = Counter(row["partition"] for row in rows)
    eda = [row for row in entities if row["partition"] == "eda"]
    targets = [row for row in eda if row["salary_target_vnd_month"] is not None]
    return {
        "rules_version": RULES_VERSION,
        "summary": {
            "raw_rows": len(rows),
            "duplicates": counts["duplicates"],
            "invalid_identity": counts["invalid_identity"],
            "out_of_scope": counts["out_of_scope"],
            "role_review": counts["role_review"],
            "eda_postings": len(eda),
            "salary_targets": len(targets),
            **({"entity_review": counts["entity_review"]} if counts["entity_review"] else {}),
        },
        "rows": rows,
        "eda": eda,
        "targets": targets,
        "review": [row for row in rows if row["review_reasons"]],
        "duplicates": [row for row in rows if row["partition"] == "duplicates"],
        "repost_groups": [
            {
                "group_id": key,
                "evidence": "same_observed_fields",
                "row_ids": [r["row_id"] for r in members],
                "posting_ids": sorted({r["posting_id"] for r in members if r["posting_id"]}),
            }
            for key, members in groups.items()
            if len(members) > 1
        ],
        "ml_state": "blocked_pending_salary_gate",
    }
