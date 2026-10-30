"""Synthetic logic cases stay test-only; report/UI checks use approved new raw sources."""

import pytest

from career_market import MarketService


def test_experience_range_retains_both_year_bounds():
    assert MarketService().normalize_experience("1 - 2 Năm") == {
        "experience_min": 1.0,
        "experience_max": 2.0,
        "experience_kind": "range",
        "experience_status": "ok",
        "experience_reason": None,
    }


@pytest.mark.parametrize("raw", [None, "", "  ", "N/A", "null", float("nan")])
def test_missing_experience_is_null_instead_of_zero(raw):
    assert MarketService().normalize_experience(raw) == {
        "experience_min": None,
        "experience_max": None,
        "experience_kind": "missing",
        "experience_status": "missing",
        "experience_reason": "missing_experience",
    }


@pytest.mark.parametrize("raw", ["Không yêu cầu kinh nghiệm", "Chưa có kinh nghiệm"])
def test_explicit_no_experience_has_zero_and_its_own_kind(raw):
    assert MarketService().normalize_experience(raw) == {
        "experience_min": 0.0,
        "experience_max": 0.0,
        "experience_kind": "no_experience",
        "experience_status": "ok",
        "experience_reason": None,
    }


@pytest.mark.parametrize("raw, years", [("2 năm", 2.0), ("1,5 năm", 1.5), (2, 2.0), (0, 0.0)])
def test_exact_experience_uses_years_and_preserves_numeric_zero_kind(raw, years):
    assert MarketService().normalize_experience(raw) == {
        "experience_min": years,
        "experience_max": years,
        "experience_kind": "exact",
        "experience_status": "ok",
        "experience_reason": None,
    }


@pytest.mark.parametrize(
    "raw, low, high, kind",
    [
        ("Trên 1 Năm", 1.0, None, "greater_than"),
        ("Dưới 1 năm", None, 1.0, "less_than"),
        ("Từ 2 năm", 2.0, None, "at_least"),
        ("2+ năm", 2.0, None, "at_least"),
        ("Tối đa 3 năm", None, 3.0, "at_most"),
    ],
)
def test_one_sided_experience_retains_open_bound_and_comparison(raw, low, high, kind):
    assert MarketService().normalize_experience(raw) == {
        "experience_min": low,
        "experience_max": high,
        "experience_kind": kind,
        "experience_status": "ok",
        "experience_reason": None,
    }


@pytest.mark.parametrize(
    "raw, low, high, kind",
    [
        ("6 tháng", 0.5, 0.5, "exact"),
        ("6 - 18 tháng", 0.5, 1.5, "range"),
        ("Dưới 6 tháng", None, 0.5, "less_than"),
        ("Trên 18 tháng", 1.5, None, "greater_than"),
        ("6+ tháng", 0.5, None, "at_least"),
    ],
)
def test_months_are_converted_to_years_without_closing_open_bounds(raw, low, high, kind):
    assert MarketService().normalize_experience(raw) == {
        "experience_min": low,
        "experience_max": high,
        "experience_kind": kind,
        "experience_status": "ok",
        "experience_reason": None,
    }


@pytest.mark.parametrize(
    "raw", ["Nhân viên", "Senior", "Junior 2", "1 - 2 - 3 năm", "2 năm abc", True]
)
def test_levels_and_malformed_experience_are_reviewed_instead_of_guessed(raw):
    assert MarketService().normalize_experience(raw) == {
        "experience_min": None,
        "experience_max": None,
        "experience_kind": "unknown",
        "experience_status": "review",
        "experience_reason": "unrecognized_experience",
    }


@pytest.mark.parametrize(
    "raw, reason",
    [
        ("-1 năm", "negative_experience"),
        ("-1 - 2 năm", "negative_experience"),
        ("3 - 1 năm", "inverted_experience_range"),
        ("61 năm", "experience_over_60_years"),
        ("1 - 61 năm", "experience_over_60_years"),
        ("Trên 61 năm", "experience_over_60_years"),
        ("Dưới -1 năm", "negative_experience"),
        ("721 tháng", "experience_over_60_years"),
    ],
)
def test_invalid_bounds_are_quarantined_with_reason(raw, reason):
    result = MarketService().normalize_experience(raw)
    assert (
        result["experience_min"],
        result["experience_max"],
        result["experience_status"],
        result["experience_reason"],
    ) == (None, None, "review", reason)


@pytest.mark.parametrize(
    "raw, low, high",
    [
        ("Từ 1 đến 2 năm", 1.0, 2.0),
        ("1,5 – 2,5 năm", 1.5, 2.5),
        ("6 tháng - 1 năm", 0.5, 1.0),
        ("1 năm - 18 tháng", 1.0, 1.5),
    ],
)
def test_range_units_and_decimal_bounds_are_preserved(raw, low, high):
    assert MarketService().normalize_experience(raw) == {
        "experience_min": low,
        "experience_max": high,
        "experience_kind": "range",
        "experience_status": "ok",
        "experience_reason": None,
    }


def test_experience_report_preserves_raw_source_identity_and_exports_the_same_rows():
    import csv
    import io

    service = MarketService()
    original = service.preview("jobs-2023", limit=1).records[0]
    report = service.experience_report("jobs-2023")
    row = report["rows"][0]
    assert (report["total_count"], report["filtered_count"]) == (2056, 2056)
    assert (row["source_id"], row["job_id"], row["job_url"], row["experience_raw"]) == (
        original.source_id,
        original.job_id,
        original.job_url,
        original.raw["exp"],
    )
    assert row["experience_raw"] == "Trên 1 Năm"
    assert (row["experience_status"], row["experience_reason"]) == ("ok", None)
    exported = list(csv.DictReader(io.StringIO(report["csv"])))
    assert len(exported) == 2056
    assert exported[0]["experience_raw"] == "Trên 1 Năm"
    assert exported[0]["job_url"] == original.job_url
    assert exported[0]["experience_min"] == "1.0"
    assert exported[0]["experience_max"] == ""


def test_experience_report_filters_status_and_kind_and_exports_only_matches():
    import csv
    import io

    service = MarketService()
    report = service.experience_report("jobs-2026", status="ok", kind="greater_than")
    assert report["total_count"] == 1550
    assert 0 < report["filtered_count"] < 1550
    assert all(row["experience_kind"] == "greater_than" for row in report["rows"])
    exported = list(csv.DictReader(io.StringIO(report["csv"])))
    assert len(exported) == report["filtered_count"]
    assert exported[0]["experience_raw"] == report["rows"][0]["experience_raw"]
    assert exported[0]["experience_max"] == ""
    empty = service.experience_report("jobs-2026", status="review", kind="greater_than")
    assert empty["rows"] == []
    assert empty["filtered_count"] == 0
    assert list(csv.DictReader(io.StringIO(empty["csv"]))) == []
    assert "experience_raw" in empty["csv"]


def test_compact_source_bounds_do_not_become_review_or_exact():
    assert MarketService().normalize_experience("Dưới 1Năm") == {
        "experience_min": None,
        "experience_max": 1.0,
        "experience_kind": "less_than",
        "experience_status": "ok",
        "experience_reason": None,
    }


@pytest.mark.parametrize("raw", ["Không yêu cầu", "Không có kinh nghiệm"])
def test_explicit_no_experience_labels_are_not_misclassified_as_missing(raw):
    assert MarketService().normalize_experience(raw) == {
        "experience_min": 0.0,
        "experience_max": 0.0,
        "experience_kind": "no_experience",
        "experience_status": "ok",
        "experience_reason": None,
    }


@pytest.mark.parametrize("raw", ["NaN", "None", "NA"])
def test_textual_null_markers_are_missing(raw):
    result = MarketService().normalize_experience(raw)
    assert (result["experience_min"], result["experience_max"], result["experience_status"]) == (
        None,
        None,
        "missing",
    )


def test_experience_page_shows_raw_clean_filters_and_download():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    page = Path(__file__).parents[1] / "pages/tools/experience.py"
    app = AppTest.from_file(str(page), default_timeout=15).run()
    assert not app.exception
    assert app.metric[0].value == "2056"
    assert app.dataframe[0].value.iloc[0]["experience_raw"] == "Trên 1 Năm"
    app.selectbox(key="experience_status").select("review").run()
    frame = app.dataframe[0].value
    assert len(frame) == 249
    assert set(frame["experience_status"]) == {"review"}
    assert "Nhân viên" in set(frame["experience_raw"])
    assert app.get("download_button")[0].proto.label == "Tải CSV đang lọc"
    app.selectbox(key="experience_kind").select("range").run()
    assert app.metric[1].value == "0"
    assert not app.dataframe
    assert not app.exception
