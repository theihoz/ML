"""Small worked examples verify distinct posting counts, not market claims."""

import csv
import io
from pathlib import Path

from streamlit.testing.v1 import AppTest

from career_market import MarketService


def test_demand_filters_distinct_postings_and_exports_matching_chart_and_table():
    rows = [
        {
            "posting_id": "fixture:1",
            "source_id": "fixture",
            "role": "Backend",
            "locations": ["HCM", "HN"],
            "work_modes": ["Remote"],
            "skills": ["Java", "Java"],
        },
        {
            "posting_id": "fixture:1",
            "source_id": "fixture",
            "role": "Backend",
            "locations": ["HCM", "HN"],
            "work_modes": ["Remote"],
            "skills": ["Java"],
        },
        {
            "posting_id": "fixture:2",
            "source_id": "fixture",
            "role": "Backend",
            "locations": ["HN"],
            "work_modes": [],
            "skills": ["Python"],
        },
        {
            "posting_id": "fixture:3",
            "source_id": "fixture",
            "role": "Mobile",
            "locations": ["HN"],
            "work_modes": [],
            "skills": ["Swift"],
        },
    ]
    service = MarketService()
    result = service.skill_demand(rows, role="Backend", locations=["HCM", "HN"])
    assert result["posting_count"] == 2
    assert result["table"] == [
        {"skill": "Java", "posting_count": 1, "share_percent": 50.0, "sample_size": 2},
        {"skill": "Python", "posting_count": 1, "share_percent": 50.0, "sample_size": 2},
    ]
    assert result["png"].startswith(b"\x89PNG")
    exported = list(csv.DictReader(io.StringIO(result["csv"].decode())))
    assert [row["skill"] for row in exported] == ["Java", "Python"]
    remote = service.skill_demand(rows, role="Backend", work_mode="Remote")
    assert remote["posting_count"] == 1
    assert remote["table"][0]["share_percent"] == 100.0


def test_dashboard_filters_real_postings_and_exposes_csv_and_png_exports():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    app.switch_page("pages/market.py").run()
    assert not app.exception
    # Two manual Mobile/Web QA titles are now review, not Mobile developers.
    assert app.metric[0].value == "293"
    assert len(app.get("download_button")) == 2
    app.selectbox(key="demand_role").select("Backend").run()
    assert not app.exception
    assert app.metric[0].value == "72"
    assert set(app.dataframe[0].value["sample_size"]) == {72}
    app.multiselect(key="demand_locations").select("HCM").select("HN").run()
    assert not app.exception
    assert int(app.metric[0].value) <= 72
