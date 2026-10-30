from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "pages/tools/sources.py"


def test_dashboard_previews_real_records_and_switches_sources():
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert app.metric[0].value == "2056"
    assert app.dataframe[0].value.iloc[0]["job_title"] == "Performance Marketing"
    assert "CC0-1.0" in app.caption[0].value
    app.selectbox[0].select("jobs-2026").run()
    assert not app.exception
    assert app.metric[0].value == "1550"
    assert app.dataframe[0].value.iloc[0]["title"] == "GẤP\nUnity Developer (2+ Yoe) – Game Mobile"
    assert "CC-BY-4.0" in app.caption[0].value
    assert any("Thiếu JD" in item.value for item in app.warning)
    assert any("nguồn EDA" in item.value for item in app.info)
    assert any("7 cột" in item.value for item in app.markdown)


def test_dashboard_shows_missing_source_error_without_crashing(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREER_MARKET_RAW_DIR", str(tmp_path))
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert "Không đọc được raw vietnamese-job-posting.csv" in app.error[0].value
    assert len(app.dataframe) == 0
