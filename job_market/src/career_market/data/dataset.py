"""BƯỚC 2 — Gộp ba nguồn thô thành bộ dữ liệu salary-v2.

Mục này làm gì: đọc 3 file CSV → áp quy tắc ở rules.py → lọc tin có lương + thuộc CNTT
→ khử trùng lặp → chia train/valid/test 70/15/15 theo công ty (không rò rỉ giữa các tập).
"""

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from ..paths import data_root, dataset_path
from .rules import (
    classify_role,
    derive_level,
    extract_skills,
    gender_requirement,
    normalize_region,
    parse_experience,
    parse_salary,
)

DATASET_VERSION = "salary-v2"
SPLIT_SEED = 42
SPLIT_SHARES = {"train": 0.70, "valid": 0.15, "test": 0.15}


def _year(value, default):
    match = re.search(r"(20\d\d)", str(value or ""))
    return int(match[1]) if match else default


def _topcv(raw):
    frame = pd.read_csv(raw / "topcv_jobs.csv")
    for row in frame.itertuples():
        yield {
            "source": "TopCV 2026",
            "title": row.title,
            "company": row.company,
            "location": row.location,
            "salary_text": row.salary,
            "experience_text": row.experience,
            "level_text": "",
            "year": _year(row.date_posted, 2026),
            "skill_text": (row.title,),
        }


def _it_posts(raw):
    frame = pd.read_csv(raw / "vietnam_it_job_posts_v1.csv")
    for row in frame.itertuples():
        try:
            listed = " ".join(json.loads(row.skills)) if isinstance(row.skills, str) else ""
        except json.JSONDecodeError:
            listed = str(row.skills)
        yield {
            "source": f"IT Jobs 2026 ({row.source_platform})",
            "title": row.title,
            "company": row.company,
            "location": row.location,
            "salary_text": row.salary,
            "experience_text": row.experience,
            "level_text": row.level,
            # posted_at của bộ này phân bố đều 2018–2025 ở mọi nền tảng nên không
            # phản ánh ngày đăng thật; dùng năm thu thập (created_at) thay thế.
            "year": _year(row.created_at, 2026),
            "skill_text": (row.title, listed, row.requirements),
        }


def _careerbuilder(raw):
    frame = pd.read_csv(raw / "vietnamese-job-posting.csv")
    frame = frame[frame["category"].fillna("").str.contains("CNTT")]
    for row in frame.itertuples():
        yield {
            "source": "CareerBuilder 2023",
            "title": row.job_title,
            "company": row.company_title,
            "location": row.location,
            "salary_text": row.salary,
            "experience_text": row.exp,
            "level_text": "",
            "year": 2023,
            "skill_text": (row.job_title, row.job_requirements, row.job_description, row.job_tags),
        }


def _company_key(name):
    text = re.sub(r"\s+", " ", str(name or "").lower())
    text = re.sub(r"^(?:pro|hot|top)\s*", "", text)
    return re.sub(r"[^\w]", "", text) or "unknown"


def _split_for(company_key):
    """Chia theo hash công ty: ổn định, tái lập được, không rò rỉ giữa các tập."""
    digest = hashlib.sha256(f"{SPLIT_SEED}:{company_key}".encode()).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    if bucket < SPLIT_SHARES["train"]:
        return "train"
    if bucket < SPLIT_SHARES["train"] + SPLIT_SHARES["valid"]:
        return "valid"
    return "test"


# Mục này: ba hàm đọc nguồn ở trên đưa mọi tin về cùng một dạng dict; build_dataset gộp lại.
def build_dataset(raw_dir=None):
    """Đọc ba nguồn thô và trả về DataFrame đã làm sạch kèm cột split."""
    raw = Path(raw_dir) if raw_dir else data_root() / "raw"
    funnel = {"raw": 0, "has_salary": 0, "it_role": 0, "deduplicated": 0}
    records = []
    for reader in (_it_posts, _topcv, _careerbuilder):
        for item in reader(raw):
            funnel["raw"] += 1
            year = min(max(item["year"], 2023), 2026)
            salary = parse_salary(item["salary_text"], year)
            if salary is None:
                continue
            funnel["has_salary"] += 1
            title = re.sub(r"\s+", " ", str(item["title"])).strip()
            role = classify_role(title)
            if role is None:
                continue
            funnel["it_role"] += 1
            years = parse_experience(item["experience_text"], title)
            skills = extract_skills(*item["skill_text"])
            records.append(
                {
                    "source": item["source"],
                    "title": title,
                    "company": re.sub(r"\s+", " ", str(item["company"])).strip(),
                    "company_key": _company_key(item["company"]),
                    "role": role,
                    "region": normalize_region(item["location"]),
                    "location_text": item["location"],
                    "experience_years": years,
                    "level": derive_level(title, years, item["level_text"]),
                    "year": year,
                    "skills": "|".join(skills),
                    "skill_count": len(skills),
                    "gender_requirement": gender_requirement(*item["skill_text"]),
                    "salary_text": item["salary_text"],
                    "salary_min": salary[0],
                    "salary_max": salary[1],
                    "salary": salary[2],
                }
            )
    frame = pd.DataFrame(records)
    frame["title_key"] = frame["title"].str.lower().str.replace(r"[^\w]", "", regex=True)
    frame = frame.drop_duplicates(["title_key", "company_key", "salary"], keep="first")
    frame = frame.drop(columns="title_key").reset_index(drop=True)
    funnel["deduplicated"] = len(frame)
    frame["split"] = frame["company_key"].map(_split_for)
    frame.insert(0, "row_id", [f"v2-{i:05d}" for i in range(len(frame))])
    return frame, funnel


def write_dataset(raw_dir=None, output=None):
    frame, funnel = build_dataset(raw_dir)
    output = Path(output) if output else dataset_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    summary = {
        "version": DATASET_VERSION,
        "rows": len(frame),
        "companies": int(frame["company_key"].nunique()),
        "funnel": funnel,
        "split": frame["split"].value_counts().to_dict(),
        "roles": frame["role"].value_counts().to_dict(),
        "sources": frame["source"].value_counts().to_dict(),
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    output.with_suffix(".json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def load_dataset():
    path = dataset_path()
    if not path.exists():
        write_dataset()
    frame = pd.read_csv(path)
    frame["skills"] = frame["skills"].fillna("")
    return frame


def skill_lists(frame):
    return frame["skills"].fillna("").map(lambda value: [s for s in value.split("|") if s])
