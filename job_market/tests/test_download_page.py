"""Smoke the independent page using real business methods and an HTTP fixture."""

import io
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "pages/tools/download.py"
ARCHIVE = Path(__file__).parent / "fixtures/download/jobs-2026-v1.zip"


def test_page_shows_license_dates_and_verified_download(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREER_MARKET_RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("CAREER_MARKET_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(ARCHIVE.read_bytes()))
    page = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not page.exception
    assert "Kaggle v2" in page.caption[0].value
    assert "CC0-1.0" in page.caption[0].value
    original_dates = page.dataframe[0].value.set_index("Loại thời gian")["Giá trị / ý nghĩa"]
    assert "announcement_date" in original_dates["Ngày đăng / thông báo"]
    assert "expiration_date" in original_dates["Hạn nộp"]
    assert original_dates["Ngày tải (UTC)"] == "Chưa xác minh"
    page.selectbox[0].select("jobs-2026").run()
    assert "CC-BY-4.0" in page.caption[0].value
    page.button[0].click().run()
    assert not page.exception
    assert "v1" in page.success[0].value
    assert "SHA-256" in page.success[0].value
    dates = page.dataframe[0].value.set_index("Loại thời gian")["Giá trị / ý nghĩa"]
    assert "date_posted" in dates["Ngày đăng / thông báo"]
    assert dates["Hạn nộp"] == "Nguồn không cung cấp"
    assert dates["Ngày cập nhật tin"] == "Nguồn không cung cấp"
    assert "+00:00" in dates["Ngày tải (UTC)"]


def test_page_surfaces_changed_source_without_overwrite(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREER_MARKET_RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("CAREER_MARKET_CACHE_DIR", str(tmp_path / "cache"))
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw_path = raw_dir / "vietnamese-job-posting.csv"
    raw_path.write_bytes(b"test-only changed raw")
    page = AppTest.from_file(str(APP), default_timeout=15).run()
    page.button[0].click().run()
    assert not page.exception
    assert "SHA-256 raw" in page.error[0].value
    assert len(page.success) == 0
    assert raw_path.read_bytes() == b"test-only changed raw"
