"""Audited source-specific labels; no inference of missing salary units."""

import csv
import hashlib
import re
from collections import defaultdict
from pathlib import Path

from .companies import canonical_name, stable_id

RAW_SHA256 = "d201d539d1bbc79a54a369eafc94d85efbb10bdece9f6ac80b9e5e4c9a0bc30c"
SOURCE = "vitthnhnguyn138/vietnam-it-job-posts"
SALARY = re.compile(r"\s*(\d+(?:[.,]\d+)?)tr\s*[-–]\s*(\d+(?:[.,]\d+)?)tr\s*₫/tháng\s*", re.I)
# Row-specific adjudication, valid only for the pinned complete source bytes.
# These titles explicitly name the occupation. No publisher skills/field/hash is used.
ACCEPTED = {
    717: ("Data/ML", "AI/NLP Engineer"),
    779: ("Data/ML", "AI Solution Architect"),
    827: ("Data/ML", "AI Engineer"),
    850: ("Fullstack", "Fullstack Engineer"),
    931: ("DevOps", "Devops & SRE"),
    971: ("Backend", "Backend Developer"),
    1046: ("Frontend", "Frontend Developer"),
    1510: ("Data/ML", "Data Scientist"),
    2111: ("Data/ML", "Data Engineer"),
    5583: ("Data/ML", "AI Engineer"),
    5831: ("Backend", "Backend Engineer"),
    6673: ("Data/ML", "AI Architect"),
    6676: ("DevOps", "DevOps / SRE / Platform Engineer"),
    6751: ("Data/ML", "Nghiên Cứu AI"),
}


def data_root():
    package = Path(__file__).resolve().parent
    bundled = package / "datasets"
    return bundled if bundled.is_dir() else package.parents[1] / "datasets"


def external_id(row):
    match = re.search(r"-(\d+)-jv/?$", row["source_url"])
    return match[1] if match else None


def adjudicate(service):
    path = data_root() / "raw/vietnam_it_job_posts_v1.csv"
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != RAW_SHA256:
        raise ValueError("Training source checksum mismatch; re-adjudication required.")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        raw = list(csv.DictReader(handle))
    versions = defaultdict(list)
    for ordinal, row in enumerate(raw, 1):
        if external_id(row):
            versions[external_id(row)].append((ordinal, row))
    accepted, ledger = [], []
    for ordinal, original in enumerate(raw, 1):
        match = SALARY.fullmatch(original["salary"])
        if not match:
            continue
        decision = "not_accepted"
        reason = (
            "No unambiguous reviewed software occupation, or duplicate/version/cohort needs review."
        )
        if ordinal in ACCEPTED:
            role, evidence = ACCEPTED[ordinal]
            if evidence.casefold() not in original["title"].casefold():
                raise ValueError("Occupation evidence mismatch.")
            linked = versions[external_id(original)]
            if ordinal == 779:
                linked = [
                    (i, item)
                    for i, item in enumerate(raw, 1)
                    if canonical_name(item["company"]) == canonical_name(original["company"])
                    and item["title"] == original["title"]
                    and item["salary"] == original["salary"]
                ]
            if len({(r["salary"], canonical_name(r["company"])) for _, r in linked}) != 1:
                raise ValueError("Accepted posting has conflicting full-source versions.")
            if not original["company"].strip() or original["company"].casefold() == "unknown":
                raise ValueError("Accepted posting lacks employer.")
            low, high = [float(value.replace(",", ".")) * 1000000 for value in match.groups()]
            if not 0 < low <= high:
                raise ValueError("Invalid salary bounds.")
            # The source does not document units for bare numeric experience.
            # Preserve it for audit, but only explicit year/month text can become a feature.
            exp_raw = original["experience"]
            experience = service.normalize_experience(
                exp_raw if re.search(r"năm|tháng|years?|months?", exp_raw, re.I) else None
            )
            location = service.normalize_locations(original["location"])
            skills = service.extract_skills(original["title"])
            row = {
                "source_id": SOURCE,
                "source_revision": 1,
                "source_raw_sha256": RAW_SHA256,
                "source_row": ordinal,
                "source_row_sha256": stable_id(original),
                "evidence_rows": [i for i, _ in linked],
                "posting_id": "vietnamworks:" + external_id(original),
                "job_id": external_id(original),
                "job_url": original["source_url"],
                "company_raw": original["company"],
                "title_raw": original["title"],
                "posting_date_raw": original["posted_at"],
                "role": role,
                "role_evidence": evidence,
                "skills": skills["skills"],
                "skill_evidence": skills["skill_evidence"],
                "locations": location["locations"],
                "work_modes": location["work_modes"],
                "experience_raw": exp_raw,
                **experience,
                "salary_raw": original["salary"],
                "salary_min": low,
                "salary_max": high,
                "salary_currency": "VND",
                "salary_period": "MONTH",
                "salary_basis": "unknown",
                "compensation_scope": "salary_components_unspecified",
                "salary_target_vnd_month": (low + high) / 2,
                "partition": "eda",
                "review_reasons": [],
                "source_license_declared": "MIT",
                "feature_evidence_scope": "original_title_and_location_only; numeric_experience_unconfirmed",
            }
            accepted.append(row)
            decision, reason = (
                "accepted",
                "Explicit original occupation title and bounded VND/month salary; unknown components/basis retained.",
            )
        ledger.append(
            {
                "source_row": ordinal,
                "source_row_sha256": stable_id(original),
                "url": original["source_url"],
                "company": original["company"],
                "title": original["title"],
                "salary": original["salary"],
                "decision": decision,
                "reason": reason,
            }
        )
    return {
        "rows": accepted,
        "review_ledger": ledger,
        "source_rows": len(raw),
        "accepted_entities": len(accepted),
        "company_count": len({canonical_name(r["company_raw"]) for r in accepted}),
        "labels_sha256": stable_id(accepted),
        "source_raw_sha256": RAW_SHA256,
        "limitations": [
            "small_exploratory_cohort",
            "title_only_skills",
            "unknown_gross_net",
            "salary_components_unspecified",
            "numeric_experience_units_unconfirmed",
        ],
    }
