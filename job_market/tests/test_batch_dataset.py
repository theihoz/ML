"""Gộp lô mới vào bộ dữ liệu và hàng đợi duyệt tay (#106), sổ nhãn đã duyệt (#107)."""

import numpy as np
import pandas as pd
import pytest

from career_market.data.batches import import_batch
from career_market.data.dataset import build_dataset, load_dataset
from career_market.data.review import load_ledger, record_review, review_key
from career_market.model.validation import latest_batch

COLUMNS = [
    "source",
    "title",
    "company",
    "location",
    "salary_text",
    "experience_text",
    "description",
    "url",
    "posted_date",
]


@pytest.fixture(scope="module")
def shipped():
    return load_dataset()


def _batch(tmp_path, rows):
    csv = tmp_path / "lo.csv"
    pd.DataFrame(rows, columns=COLUMNS).to_csv(csv, index=False)
    directory = tmp_path / "batches"
    assert import_batch(csv, directory=directory)["status"] == "imported"
    return directory


def _row(**overrides):
    row = {
        "source": "Lô thử",
        "title": "Senior Backend Developer (Java)",
        "company": "Công ty Thử Nghiệm Mới",
        "location": "Hà Nội",
        "salary_text": "30 - 40 triệu",
        "experience_text": "5 năm",
        "description": "Java, Spring Boot, SQL, Docker",
        "url": "https://example.test/job/1",
        "posted_date": "2026-11-01",
    }
    return {**row, **overrides}


def test_valid_batch_posting_is_labelled_like_the_old_sources(tmp_path, shipped):
    batches = _batch(tmp_path, [_row()])
    frame, funnel = build_dataset(batches=batches, ledger=tmp_path / "none.csv")
    added = frame[frame["batch"] != ""]
    assert len(added) == 1 and len(frame) == len(shipped) + 1
    row = added.iloc[0]
    assert row["role"] == "Backend Developer"
    assert row["level"] == "Senior"
    assert (row["salary_min"], row["salary_max"], row["salary"]) == (30, 40, 35)
    assert {"Java", "Spring Boot", "SQL", "Docker"} <= set(row["skills"].split("|"))
    assert funnel["review_queue"] == 0


def test_negotiable_salary_goes_to_the_queue_not_the_dataset(tmp_path, shipped):
    batches = _batch(
        tmp_path,
        [
            _row(salary_text="Thoả thuận", url="https://example.test/job/2"),
            _row(title="Chuyên viên số hoá XYZ", url="https://example.test/job/3"),
        ],
    )
    frame, funnel = build_dataset(batches=batches, ledger=tmp_path / "none.csv")
    assert len(frame) == len(shipped)
    reasons = {row["url"]: row["reason"] for row in frame.attrs["review_queue"]}
    assert reasons == {
        "https://example.test/job/2": "lương thoả thuận",
        "https://example.test/job/3": "không phân loại được vai trò",
    }
    assert funnel["review_queue"] == 2


def test_batch_posting_duplicating_an_old_source_is_dropped(tmp_path, shipped):
    old = shipped[shipped["source_url"].fillna("") != ""].iloc[0]
    batches = _batch(tmp_path, [_row(url=old["source_url"], title="Một chức danh khác hẳn")])
    frame, _ = build_dataset(batches=batches, ledger=tmp_path / "none.csv")
    assert len(frame) == len(shipped)


def test_new_posting_of_a_train_company_lands_in_train(tmp_path, shipped):
    company = shipped.loc[shipped["split"] == "train", "company"].iloc[0]
    batches = _batch(tmp_path, [_row(company=company, url="https://example.test/job/4")])
    frame, _ = build_dataset(batches=batches, ledger=tmp_path / "none.csv")
    assert frame.loc[frame["batch"] != "", "split"].tolist() == ["train"]


def test_reviewed_label_is_applied_at_the_next_build(tmp_path, shipped):
    batches = _batch(tmp_path, [_row(salary_text="Thoả thuận", url="https://example.test/job/5")])
    ledger = tmp_path / "reviewed.csv"
    key = review_key("https://example.test/job/5", "", "")
    record_review(key, "accept", path=ledger, salary_min=28, salary_max=36, reviewer="test")
    frame, funnel = build_dataset(batches=batches, ledger=ledger)
    row = frame[frame["batch"] != ""].iloc[0]
    assert row["salary"] == 32 and not row["one_sided"]
    assert funnel["review_queue"] == 0
    record_review(key, "reject", path=ledger, reviewer="test")
    assert load_ledger(ledger)[key]["decision"] == "reject"
    frame, funnel = build_dataset(batches=batches, ledger=ledger)
    assert (frame["batch"] != "").sum() == 0 and funnel["review_rejected"] == 1


def test_validation_scores_the_latest_batch_only():
    valid = pd.DataFrame({"salary": [10.0, 20.0], "batch": ["", "20261101T000000-a"]})
    test = pd.DataFrame({"salary": [30.0, 40.0], "batch": ["20261102T000000-b", ""]})
    parts = {"valid": valid, "test": test}
    predicted = {"valid": np.array([10.0, 22.0]), "test": np.array([33.0, 40.0])}
    result = latest_batch(parts, predicted)
    assert result["batch"] == "20261102T000000-b" and result["n"] == 1
    assert result["MAE"] == pytest.approx(3.0)
    empty = latest_batch(
        {"valid": valid.assign(batch=""), "test": test.assign(batch="")}, predicted
    )
    assert empty["status"] == "chưa có lô mới"


def test_shipped_validation_reports_the_latest_batch_section():
    from career_market.model.validation import load_validation

    assert "latest_batch" in load_validation()


def test_ledger_rejects_labels_outside_the_vocabulary(tmp_path):
    with pytest.raises(ValueError, match="vai trò"):
        record_review("k", "accept", path=tmp_path / "r.csv", role="Backend Dev")
    with pytest.raises(ValueError, match="kỹ năng"):
        record_review("k", "accept", path=tmp_path / "r.csv", skills="Java|Jvaa")


def test_shipped_ai_audit_sample_error_rates():
    from career_market.data.review import audit_error_rates
    from career_market.paths import data_root

    review = pd.read_csv(
        data_root() / "labels/2026-11-06/audit_sample_ai_67.csv", dtype=str, keep_default_na=False
    )
    rates = audit_error_rates(review).set_index("Nhãn")["Tỉ lệ sai %"]
    assert rates["Nhãn lương"] == 0
    assert rates["Vai trò"] == pytest.approx(2 / 67 * 100)
    assert rates["Cấp bậc"] == pytest.approx(1 / 67 * 100)
