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
from .batches import batches_dir, load_batch, stored_batches
from .review import (
    QUEUE_COLUMNS,
    ledger_salary,
    load_ledger,
    queue_path,
    review_key,
    salary_reason,
)
from .rules import (
    _EXCLUDED,
    classify_role,
    company_type,
    derive_level,
    extract_skills,
    gender_requirement,
    is_synthetic,
    normalize_region,
    normalize_work_mode,
    one_sided,
    parse_experience,
    parse_salary,
    platform,
)

DATASET_VERSION = "salary-v2"
SPLIT_SEED = 42
SPLIT_SHARES = {"train": 0.70, "valid": 0.15, "test": 0.15}
# Cách suy đầu còn lại của tin chỉ ghi một con số lương ("Tới X", "Từ X"), #118:
#   ratio    tỉ lệ cao/thấp trung vị của tin ghi đủ hai đầu cùng nguồn (#81, mặc định)
#   expand30 luật cố định ×0.7 / ×1.3
#   point    dùng đúng con số đó làm nhãn điểm
SINGLE_SALARY_RULES = ("ratio", "expand30", "point")


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
            "source_url": getattr(row, "url", ""),
            "work_mode": None,
            "field": "",
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
            "source_url": getattr(row, "source_url", ""),
            "work_mode": getattr(row, "mode", None),
            "field": field if isinstance(field := getattr(row, "field", ""), str) else "",
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
            "source_url": getattr(row, "job_url", ""),
            "work_mode": None,
            "field": "",
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


def _batch_items(directory):
    """Tin của mọi lô đã nhập (#105), cùng dạng dict với ba nguồn thô (#106)."""
    for manifest in stored_batches(directory):
        imported = _year(manifest["imported_at"], 2026)
        for row in load_batch(manifest, directory).itertuples():
            yield {
                "source": row.source,
                "title": row.title,
                "company": row.company,
                "location": row.location,
                "salary_text": row.salary_text,
                "experience_text": row.experience_text,
                "level_text": "",
                "year": _year(row.posted_date, imported),
                "skill_text": (row.title, row.description),
                "source_url": row.url,
                "work_mode": None,
                "field": "",
                "batch": manifest["id"],
            }


def _queue(queue, item, key, reason):
    queue.append(
        {
            "key": key,
            "batch": item["batch"],
            "source": item["source"],
            "title": item["title"],
            "company": item["company"],
            "salary_text": item["salary_text"],
            "reason": reason,
            "url": item["source_url"],
        }
    )


# Mục này: các hàm đọc nguồn ở trên đưa mọi tin về cùng một dạng dict; build_dataset gộp lại.
def build_dataset(raw_dir=None, batches=None, ledger=None, single_salary_rule="ratio"):
    """Đọc ba nguồn thô và mọi lô đã nhập, trả về DataFrame đã làm sạch kèm cột split.

    Tin sinh tự động bị loại trước khi đọc lương (#81). Tin chỉ ghi một đầu lương được tính
    lại bằng tỉ lệ cao/thấp trung vị của tin ghi đủ hai đầu trong tập train cùng nguồn.
    Sổ nhãn đã duyệt được áp dụng trước khi chia tập; tin lô mới không gắn được nhãn vào
    hàng đợi duyệt tay (``frame.attrs["review_queue"]``).
    """
    if single_salary_rule not in SINGLE_SALARY_RULES:
        raise ValueError(f"Quy tắc lương một số không hợp lệ: {single_salary_rule}")
    raw = Path(raw_dir) if raw_dir else data_root() / "raw"
    batch_root = Path(batches) if batches else batches_dir()
    reviewed = load_ledger(ledger)
    funnel = {
        "raw": 0,
        "synthetic_removed": 0,
        "review_rejected": 0,
        "has_salary": 0,
        "it_role": 0,
        "review_queue": 0,
        "deduplicated": 0,
    }
    records, queue = [], []
    sources = [reader(raw) for reader in (_it_posts, _topcv, _careerbuilder)]
    if batch_root.is_dir():
        sources.append(_batch_items(batch_root))
    for stream in sources:
        for item in stream:
            item.setdefault("batch", "")
            funnel["raw"] += 1
            if is_synthetic(item["source_url"]):
                funnel["synthetic_removed"] += 1
                continue
            key = review_key(item["source_url"], item["title"], item["company"])
            entry = reviewed.get(key)
            if entry and entry["decision"] == "reject":
                funnel["review_rejected"] += 1
                continue
            year = min(max(item["year"], 2023), 2026)
            manual = ledger_salary(entry) if entry else None
            salary = manual or parse_salary(item["salary_text"], year)
            if salary is None:
                if item["batch"]:
                    _queue(queue, item, key, salary_reason(item["salary_text"]))
                continue
            funnel["has_salary"] += 1
            title = re.sub(r"\s+", " ", str(item["title"])).strip()
            role = (entry and entry["role"]) or classify_role(title)
            if role is None:
                if item["batch"] and not _EXCLUDED.search(title):
                    _queue(queue, item, key, "không phân loại được vai trò")
                continue
            funnel["it_role"] += 1
            years = parse_experience(item["experience_text"], title)
            skills = extract_skills(*item["skill_text"])
            if entry and entry["skills"]:
                skills = [s for s in entry["skills"].split("|") if s]
            company = re.sub(r"\s+", " ", str(item["company"])).strip()
            records.append(
                {
                    "source": item["source"],
                    "platform": platform(item["source"]),
                    "title": title,
                    "company": company,
                    "company_key": _company_key(item["company"]),
                    "company_type": company_type(company, item["field"]),
                    "role": role,
                    "region": normalize_region(item["location"]),
                    "location_text": item["location"],
                    "work_mode": normalize_work_mode(item["work_mode"]),
                    "experience_years": years,
                    "level": (entry and entry["level"])
                    or derive_level(title, years, item["level_text"]),
                    "year": year,
                    "skills": "|".join(skills),
                    "skill_count": len(skills),
                    "gender_requirement": gender_requirement(*item["skill_text"]),
                    "salary_text": item["salary_text"],
                    "one_sided": one_sided(item["salary_text"]) and not manual,
                    "salary_min": salary[0],
                    "salary_max": salary[1],
                    "salary": salary[2],
                    "source_url": item["source_url"],
                    "batch": item["batch"],
                }
            )
    frame = pd.DataFrame(records)
    frame["split"] = frame["company_key"].map(_split_for)
    ratios = {
        "ratio": lambda: _one_sided_ratios(frame),
        "expand30": dict,
        "point": lambda: {source: 1.0 for source in frame["source"].unique()},
    }[single_salary_rule]()
    for index in frame.index[frame["one_sided"]]:
        row = frame.loc[index]
        salary = parse_salary(row["salary_text"], row["year"], ratios.get(row["source"]))
        if salary is None:
            frame = frame.drop(index)
            continue
        frame.loc[index, ["salary_min", "salary_max", "salary"]] = salary
    # Tin lô mới trùng URL với tin đã có (nguồn cũ hoặc lô trước) bị loại.
    urls = frame["source_url"].fillna("").astype(str)
    frame = frame[~((frame["batch"] != "") & (urls != "") & urls.duplicated(keep="first"))]
    frame["title_key"] = frame["title"].str.lower().str.replace(r"[^\w]", "", regex=True)
    frame = frame.drop_duplicates(["title_key", "company_key", "salary"], keep="first")
    frame = frame.drop(columns="title_key").reset_index(drop=True)
    funnel["deduplicated"] = len(frame)
    funnel["review_queue"] = len(queue)
    frame.attrs["review_queue"] = queue
    frame.insert(0, "row_id", [f"v2-{i:05d}" for i in range(len(frame))])
    frame.attrs["one_sided_ratio"] = ratios
    frame.attrs["single_salary_rule"] = single_salary_rule
    return frame, funnel


def _one_sided_ratios(frame):
    """Tỉ lệ cao/thấp trung vị theo nguồn, chỉ trên tin train ghi đủ hai đầu khác nhau."""
    two_sided = frame[
        (frame["split"] == "train")
        & ~frame["one_sided"]
        & (frame["salary_max"] > frame["salary_min"])
    ]
    ratio = two_sided["salary_max"] / two_sided["salary_min"]
    overall = float(ratio.median())
    by_source = ratio.groupby(two_sided["source"]).agg(["median", "size"])
    return {
        source: round(float(row["median"]) if row["size"] >= 30 else overall, 4)
        for source, row in by_source.iterrows()
    } | {source: round(overall, 4) for source in set(frame["source"]) - set(by_source.index)}


def write_dataset(
    raw_dir=None, output=None, batches=None, ledger=None, queue=None, single_salary_rule="ratio"
):
    frame, funnel = build_dataset(
        raw_dir, batches=batches, ledger=ledger, single_salary_rule=single_salary_rule
    )
    output = Path(output) if output else dataset_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    queue_file = Path(queue) if queue else (output.parent / queue_path().name)
    pd.DataFrame(frame.attrs.get("review_queue", []), columns=QUEUE_COLUMNS).to_csv(
        queue_file, index=False
    )
    summary = {
        "version": DATASET_VERSION,
        "rows": len(frame),
        "companies": int(frame["company_key"].nunique()),
        "funnel": funnel,
        "single_salary_rule": single_salary_rule,
        "one_sided_ratio": frame.attrs.get("one_sided_ratio", {}),
        "split": frame["split"].value_counts().to_dict(),
        "roles": frame["role"].value_counts().to_dict(),
        "sources": frame["source"].value_counts().to_dict(),
        "batches": frame.loc[frame["batch"] != "", "batch"].value_counts().to_dict(),
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
    frame = pd.read_csv(path, dtype={"batch": str})
    frame["skills"] = frame["skills"].fillna("")
    if "batch" in frame:
        frame["batch"] = frame["batch"].fillna("")
    return frame


def skill_lists(frame):
    return frame["skills"].fillna("").map(lambda value: [s for s in value.split("|") if s])
