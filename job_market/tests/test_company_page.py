"""Streamlit seam consumes synthetic prepared rows, including parent overlays."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from career_market import MarketService

PAGE = Path(__file__).parents[1] / "pages/tools/companies.py"


def test_company_page_displays_the_service_groups_provenance_and_csv():
    rows = [
        {
            "source_id": "fixture",
            "posting_id": "1",
            "company_raw": " Alpha ",
            "locations": ["HCM", "HN"],
            "salary_label_status": "accepted",
        },
        {"source_id": "fixture", "posting_id": "2", "company_raw": "ALPHA"},
        {"source_id": "fixture", "posting_id": "3", "company_raw": ""},
    ]
    app = AppTest.from_file(str(PAGE))
    app.session_state["company_prepared_rows"] = rows
    app.run()
    assert not app.exception
    expected = MarketService().company_report(rows)
    assert [m.value for m in app.metric][:5] == ["3", "3", "1", "2", "1"]
    assert app.dataframe[0].value["group_id"].tolist() == [
        r["group_id"] for r in expected["aliases"]
    ]
    assert app.dataframe[1].value["group_id"].tolist() == [
        r["group_id"] for r in expected["groups"]
    ]
    assert app.dataframe[2].value["source_id"].tolist() == ["fixture"] * 3
    assert len(app.get("download_button")) == 4
    assert any("70/15/15" in text.value for text in app.info)
    assert app.session_state["company_prepared_rows"] == rows


def test_company_page_explains_why_two_yody_labels_cannot_fill_three_sets():
    rows = [
        {
            "source_id": "fixture",
            "posting_id": key,
            "company_raw": "YODY",
            "salary_target_vnd_month": target,
            "salary_basis": "unknown",
            "compensation_scope": "advertised_monthly_income",
        }
        for key, target in [("1", 27_500_000), ("2", 37_500_000)]
    ]
    app = AppTest.from_file(str(PAGE))
    app.session_state["company_prepared_rows"] = rows
    app.run()
    assert not app.exception
    assert any(
        "YODY" in warning.value and "train/validation/test" in warning.value
        for warning in app.warning
    )
    assert [m.value for m in app.metric][-3:] == ["2", "1", "1"]
