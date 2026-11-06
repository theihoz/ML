"""Mẫu duyệt nhãn: đối chiếu nhãn tự động với người duyệt để đo độ chính xác (#79).

``review_sample`` lấy mẫu phân tầng theo nguồn và vai trò, đặt nhãn tự động cạnh dữ liệu thô
mà người duyệt cần (chuỗi lương, chuỗi kinh nghiệm, cấp bậc nguồn, đoạn văn quanh mỗi kỹ năng).
Người duyệt điền các cột ``review_*``; ``score_review`` tính độ chính xác của từng loại nhãn.
"""

import re

import numpy as np
import pandas as pd

from .salary_dataset import (
    _SKILL_PATTERNS,
    _careerbuilder,
    _company_key,
    _it_posts,
    _topcv,
    data_root,
    load_dataset,
)

REVIEW_COLUMNS = {
    "review_salary_ok": "Nhãn lương (thấp/cao/trung điểm) đọc đúng chuỗi lương: 1/0",
    "review_role_ok": "Vai trò gán đúng chức danh: 1/0",
    "review_level_ok": "Cấp bậc đúng với chức danh/kinh nghiệm/cấp bậc nguồn: 1/0",
    "review_experience_ok": "Số năm kinh nghiệm đọc đúng chuỗi kinh nghiệm: 1/0 (trống nếu nguồn không ghi)",
    "review_skills_wrong": "Kỹ năng gán sai (cách nhau bằng |), để trống nếu không có",
    "review_note": "Ghi chú tự do",
}
CONTEXT = 45


def _raw_records(raw_dir):
    for reader in (_it_posts, _topcv, _careerbuilder):
        for item in reader(raw_dir):
            title = re.sub(r"\s+", " ", str(item["title"])).strip()
            text = " \n ".join(str(t) for t in item["skill_text"] if isinstance(t, str))
            yield {
                "title": title,
                "company_key": _company_key(item["company"]),
                "salary_text": item["salary_text"],
                "experience_text": item["experience_text"],
                "level_text": item["level_text"],
                "skill_source": re.sub(r"<[^>]+>", " ", text),
            }


def _skill_context(skills, text):
    """Đoạn văn quanh chỗ khớp đầu tiên của từng kỹ năng, để người duyệt xem có khớp nhầm."""
    parts = []
    for name in filter(None, str(skills or "").split("|")):
        match = _SKILL_PATTERNS[name].search(text)
        if match:
            start, end = max(0, match.start() - CONTEXT), match.end() + CONTEXT
            snippet = re.sub(r"\s+", " ", text[start:end]).strip()
            parts.append(f"{name}: …{snippet}…")
    return " || ".join(parts)


def review_sample(size=200, seed=42, raw_dir=None):
    """Mẫu phân tầng theo nguồn (tỉ lệ thuận, mỗi nguồn ≥ 10 tin) rồi rải đều vai trò."""
    frame = load_dataset()
    raw = pd.DataFrame(_raw_records(raw_dir or data_root() / "raw"))
    raw = raw.drop_duplicates(["title", "company_key", "salary_text"])
    shares = frame["source"].value_counts(normalize=True)
    quotas = (shares * size).round().clip(lower=10).astype(int)
    rng = np.random.default_rng(seed)
    picked = []
    for source, quota in quotas.items():
        pool = frame[frame["source"] == source]
        # Xáo rồi xen kẽ vai trò để mẫu không dồn vào vai trò phổ biến.
        order = pool.assign(_r=rng.random(len(pool))).sort_values("_r")
        order["_rank"] = order.groupby("role").cumcount()
        picked.append(order.sort_values(["_rank", "_r"]).head(quota))
    sample = pd.concat(picked).drop(columns=["_r", "_rank"])
    sample = sample.merge(raw, on=["title", "company_key", "salary_text"], how="left")
    sample["skill_context"] = [
        _skill_context(skills, str(text))
        for skills, text in zip(sample["skills"], sample["skill_source"])
    ]
    keep = [
        "row_id",
        "source",
        "title",
        "salary_text",
        "salary_min",
        "salary_max",
        "salary",
        "role",
        "experience_text",
        "experience_years",
        "level_text",
        "level",
        "skills",
        "skill_context",
    ]
    sample = sample[keep].sort_values("row_id").reset_index(drop=True)
    for column in REVIEW_COLUMNS:
        sample[column] = ""
    return sample


def score_review(review):
    """Tỉ lệ đúng của từng loại nhãn trên các dòng người duyệt đã chấm."""
    result = {}
    for field in ("salary", "role", "level", "experience"):
        values = pd.to_numeric(review[f"review_{field}_ok"], errors="coerce").dropna()
        result[field] = {
            "reviewed": int(len(values)),
            "correct": int(values.sum()),
            "accuracy_pct": float(values.mean() * 100) if len(values) else None,
        }
    assigned = review["skills"].fillna("").map(lambda s: [x for x in s.split("|") if x])
    wrong = review["review_skills_wrong"].fillna("").map(lambda s: [x for x in s.split("|") if x])
    total = int(assigned.map(len).sum())
    errors = int(wrong.map(len).sum())
    result["skills"] = {
        "assigned": total,
        "wrong": errors,
        "precision_pct": float((total - errors) / total * 100) if total else None,
        "most_wrong": pd.Series([x for row in wrong for x in row])
        .value_counts()
        .head(10)
        .to_dict(),
    }
    return result
