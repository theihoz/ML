"""Small synthetic inputs below exercise logic only; they are not market data."""

import csv
import io
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from career_market import MarketService


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("HCM", "HCM"),
        ("TP.HCM", "HCM"),
        ("ho chi minh", "HCM"),
        ("Hồ Chí Minh", "HCM"),
        ("HN", "HN"),
        ("Ha Noi", "HN"),
        ("Hà Nội", "HN"),
    ],
)
def test_location_aliases_share_canonical_labels_and_keep_evidence(raw, canonical):
    result = MarketService().normalize_locations(raw)
    assert result == {
        "locations": [canonical],
        "location_status": "normalized",
        "location_aliases": {raw: canonical},
        "location_unresolved": [],
        "work_modes": [],
        "location_reason": "Khớp toàn bộ nhãn địa điểm đã xác minh.",
    }


@pytest.mark.parametrize(
    "raw",
    ["123 Điện Biên Phủ", "Điện Biên Phủ", "12 Hà Nội, phường 3", "HCM City Mall"],
)
def test_addresses_and_unknown_labels_remain_unresolved_instead_of_substring_matches(raw):
    result = MarketService().normalize_locations(raw)
    assert result["locations"] == []
    assert result["location_status"] == "review"
    assert result["location_aliases"] == {}
    assert result["location_unresolved"] == [raw]
    assert result["work_modes"] == []
    assert "Chưa đủ chứng cứ" in result["location_reason"]


@pytest.mark.parametrize("raw", [None, "", " \t\n"])
def test_missing_location_is_distinct_from_an_unresolved_address(raw):
    result = MarketService().normalize_locations(raw)
    assert result["location_status"] == "missing"
    assert result["locations"] == []
    assert result["location_aliases"] == {}
    assert result["location_unresolved"] == []
    assert "Thiếu" in result["location_reason"]


def test_new_scope_hcm_label_keeps_suffix_as_evidence_and_explains_comparability():
    raw = "Hồ Chí Minh (mới)"
    result = MarketService().normalize_locations(raw)
    assert result["locations"] == ["HCM"]
    assert result["location_aliases"] == {raw: "HCM"}
    assert result["location_status"] == "normalized"
    assert "(mới)" in result["location_reason"]
    assert "không" in result["location_reason"]
    assert "qua năm" in result["location_reason"]


@pytest.mark.parametrize(
    ("raw", "locations", "unresolved"),
    [
        ("Hồ Chí Minh | Hà Nội", ["HCM", "HN"], []),
        ("Hà Nội & Hồ Chí Minh (mới)", ["HN", "HCM"], []),
        ("HCM | TP.HCM | HN", ["HCM", "HN"], []),
        ("HN & 2 nơi khác", ["HN"], ["2 nơi khác"]),
        ("HCM | 123 Điện Biên Phủ", ["HCM"], ["123 Điện Biên Phủ"]),
    ],
)
def test_source_separators_allow_whole_aliases_without_guessing_remaining_labels(
    raw, locations, unresolved
):
    result = MarketService().normalize_locations(raw)
    assert result["locations"] == locations
    assert result["location_unresolved"] == unresolved
    assert result["location_status"] == ("review" if unresolved else "normalized")
    assert result["work_modes"] == []
    if "(mới)" in raw:
        assert "Hồ Chí Minh (mới)" in result["location_aliases"]
        assert "qua năm" in result["location_reason"]


@pytest.mark.parametrize(
    "raw", ["Bình Dương", "Điện Biên", "Đà Nẵng", "Đà Nẵng (mới)", "Bắc Ninh (mới)"]
)
def test_verified_source_province_labels_are_retained_without_boundary_merges(raw):
    result = MarketService().normalize_locations(raw)
    assert result["locations"] == [raw]
    assert result["location_aliases"] == {raw: raw}
    assert result["location_status"] == "normalized"
    assert result["location_unresolved"] == []
    if "(mới)" in raw:
        assert "qua năm" in result["location_reason"]


def test_location_report_filters_real_source_aliases_and_exports_raw_clean_csv():
    report = MarketService().location_report("jobs-2026", location="HCM", status="normalized")
    assert report["source_id"] == "jobs-2026"
    assert report["raw_row_count"] == 1550
    assert "HN" in report["location_options"]
    assert report["rows"]
    assert all("HCM" in json.loads(row["locations"]) for row in report["rows"])
    alias = next(row for row in report["alias_table"] if row["location_raw"] == "Hồ Chí Minh (mới)")
    assert alias["raw_rows"] == 326
    assert json.loads(alias["locations"]) == ["HCM"]
    exported = list(csv.DictReader(io.StringIO(report["csv"])))
    assert len(exported) == len(report["rows"])
    assert all(row["location_status"] == "normalized" for row in exported)
    assert all("HCM" in json.loads(row["locations"]) for row in exported)
    assert any(row["location_raw"] == "Hồ Chí Minh (mới)" for row in exported)
    assert all(row["source_id"] == "jobs-2026" and row["job_url"] for row in exported)
    assert all("qua năm" in row["location_reason"] for row in exported)


def test_location_page_shows_raw_aliases_filters_and_csv_download():
    page = Path(__file__).parents[1] / "pages/tools/locations.py"
    app = AppTest.from_file(str(page), default_timeout=15).run()
    assert not app.exception
    assert app.metric[0].value == "2056"
    assert "Hồ Chí Minh" in app.dataframe[0].value["location_raw"].tolist()
    app.selectbox(key="location_source").select("jobs-2026").run()
    assert not app.exception
    assert app.metric[0].value == "1550"
    assert "Hồ Chí Minh (mới)" in app.dataframe[0].value["location_raw"].tolist()
    app.selectbox(key="canonical_location").select("HCM").run()
    app.selectbox(key="location_status").select("review").run()
    assert not app.exception
    table = app.dataframe[1].value
    assert not table.empty
    assert set(table["location_status"]) == {"review"}
    assert all("HCM" in json.loads(value) for value in table["locations"])
    assert "Hồ Chí Minh (mới) & 2 nơi khác" in table["location_raw"].tolist()
    assert app.get("download_button")[0].proto.label == "Tải CSV raw–chuẩn đang lọc"
    assert any("cùng phạm vi địa giới qua năm" in item.value for item in app.info)


def test_separator_only_text_requires_review_instead_of_claiming_a_verified_location():
    result = MarketService().normalize_locations(" | & ")
    assert result["location_status"] == "review"
    assert result["locations"] == []
    assert result["location_unresolved"] == [" | & "]


def test_remote_is_independent_from_multiple_physical_locations():
    result = MarketService().normalize_locations("HCM/HN/Remote")
    assert result["locations"] == ["HCM", "HN"]
    assert result["work_modes"] == ["Remote"]
    assert result["location_unresolved"] == []


def test_location_union_and_remote_filters_count_a_posting_only_once():
    rows = [
        {
            "source_id": "fixture",
            "job_url": "https://example.org/job/1?utm_source=one",
            "locations": ["HCM", "HN"],
            "work_modes": ["Remote"],
        },
        {
            "source_id": "fixture",
            "job_url": "https://example.org/job/1?utm_source=two",
            "locations": ["HCM", "HN"],
            "work_modes": ["Remote"],
        },
        {
            "source_id": "fixture",
            "job_url": "https://example.org/job/2",
            "locations": ["HN"],
            "work_modes": [],
        },
    ]
    service = MarketService()
    assert len(service.select_locations(rows, locations=["HCM", "HN"])) == 2
    assert len(service.select_locations(rows, locations=["HCM", "HN"], work_mode="Remote")) == 1
