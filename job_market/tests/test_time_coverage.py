from pathlib import Path

from streamlit.testing.v1 import AppTest

from career_market import MarketService


def test_time_coverage_uses_posting_dates_and_does_not_invent_cross_source_trends():
    rows = [
        {
            "source_id": "a",
            "posting_id": "a1",
            "posting_date": "2023-02-20",
            "date_kind": "posting",
            "partition": "eda",
            "raw": {"expiration_date": "2029-01-01"},
        },
        {
            "source_id": "b",
            "posting_id": "b1",
            "posting_date": "2025-12-25",
            "date_kind": "posting",
            "partition": "eda",
        },
        {
            "source_id": "b",
            "posting_id": "b2",
            "posting_date": "2026-01-08",
            "date_kind": "posting",
            "partition": "eda",
        },
        {
            "source_id": "b",
            "posting_id": "b3",
            "posting_date": "2027-01-01",
            "date_kind": "deadline",
            "partition": "eda",
        },
    ]
    report = MarketService().time_coverage(rows)
    assert report["status"] == "insufficient_comparability"
    second = next(row for row in report["coverage"] if row["source_id"] == "b")
    assert second["years"] == [2025, 2026]
    assert second["date_to"] == "2026-01-08"
    assert second["missing_posting_dates"] == 1
    assert "2029" not in str(report["periods"])
    assert "2027" not in str(report["periods"])


def test_coverage_page_discloses_real_source_years_and_insufficient_evidence():
    page = Path(__file__).parents[1] / "pages/tools/time_coverage.py"
    app = AppTest.from_file(str(page), default_timeout=30).run()
    assert not app.exception
    table = app.dataframe[0].value.set_index("source_id")
    assert table.loc["jobs-2023", "date_from"] == "2023-02-16"
    assert list(table.loc["jobs-2026", "years"]) == [2025, 2026]
    assert "Chưa đủ cơ sở" in app.warning[0].value
    assert len(app.get("download_button")) == 2
