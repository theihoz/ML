"""Bộ dữ liệu chỉ gồm tin thật, hệ số một đầu lương ước lượng từ dữ liệu, đặc trưng mới (#81)."""

import json

import pytest

from career_market.salary_dataset import (
    company_type,
    dataset_path,
    is_synthetic,
    load_dataset,
    normalize_work_mode,
    parse_salary,
)


def test_synthetic_history_rows_are_recognised_by_their_url():
    assert is_synthetic(
        "https://careerviet.vn/vi/tim-viec-lam/backend-engineer-x-hist201800023.html"
    )
    assert is_synthetic("https://www.vietnamworks.com/fpga-senior-engineer-ghn-hist202200198-jv")
    assert not is_synthetic(
        "https://www.vietnamworks.com/senior-data-engineer-techcomlife-2060568-jv"
    )
    assert not is_synthetic(None)


def test_dataset_holds_only_real_postings_and_reports_what_was_removed():
    frame = load_dataset()
    assert not frame["source_url"].fillna("").str.contains("hist").any()
    summary = json.loads(dataset_path().with_suffix(".json").read_text(encoding="utf-8"))
    assert summary["funnel"]["synthetic_removed"] > 2000
    assert len(frame) == summary["rows"] < 2000


def test_one_sided_salaries_use_a_ratio_estimated_from_two_sided_postings():
    summary = json.loads(dataset_path().with_suffix(".json").read_text(encoding="utf-8"))
    ratios = summary["one_sided_ratio"]
    assert ratios and all(1.1 < r < 1.8 for r in ratios.values())
    assert parse_salary("Tới 30 triệu", ratio=1.25) == (24.0, 30.0, 27.0)
    assert parse_salary("Từ 20 triệu", ratio=1.25) == (20.0, 25.0, 22.5)
    # Không truyền hệ số thì giữ luật cũ (0.7 / 1.3).
    assert parse_salary("Tới 30 triệu") == (21.0, 30.0, 25.5)


@pytest.mark.parametrize(
    ("raw", "mode"),
    [
        ("Toàn thời gian", "Toàn thời gian"),
        ("Làm việc từ xa", "Từ xa"),
        ("Thực tập", "Thực tập"),
        ("Bán thời gian", "Bán thời gian"),
        (None, "Không rõ"),
    ],
)
def test_work_mode_is_normalised(raw, mode):
    assert normalize_work_mode(raw) == mode


@pytest.mark.parametrize(
    ("company", "field", "kind"),
    [
        ("NGÂN HÀNG TMCP QUÂN ĐỘI – MBBANK", "", "Ngân hàng / Tài chính"),
        ("Techcombank", "", "Ngân hàng / Tài chính"),
        ("Công ty ABC", "Ngân hàng - Tài chính", "Ngân hàng / Tài chính"),
        ("FPT Software", "", "Outsourcing / Gia công"),
        ("Bosch Vietnam", "", "Công ty nước ngoài"),
        ("CÔNG TY CỔ PHẦN ĐẦU TƯ CÔNG NGHỆ THIÊN ÂN", "", "Khác"),
    ],
)
def test_company_type_from_name_and_field(company, field, kind):
    assert company_type(company, field) == kind


def test_dataset_carries_the_new_feature_columns():
    frame = load_dataset()
    assert {"platform", "work_mode", "company_type", "source_url"} <= set(frame.columns)
    assert frame["work_mode"].notna().all() and frame["company_type"].notna().all()
