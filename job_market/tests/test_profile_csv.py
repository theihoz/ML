"""Synthetic input profiles test upload behavior; not a market dataset."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from career_market import MarketError, MarketService


def test_csv_mapping_preserves_order_raw_aliases_and_per_row_errors():
    content = "nghe,nam,tech,noilam\nBackend,2,ReactJS; Python,ho chi minh\nKhông rõ,,Unknown,HN\n".encode()
    result = MarketService().preview_profiles(
        content, {"role": "nghe", "experience": "nam", "skills": "tech", "location": "noilam"}
    )
    assert result["row_count"] == 2
    assert result["valid_count"] == 1
    assert [r["row_id"] for r in result["rows"]] == [1, 2]
    first, second = result["rows"]
    assert first["role"] == "Backend"
    assert first["locations"] == ["HCM"]
    assert set(first["skills"]) == {"React", "Python"}
    assert first["raw"]["noilam"] == "ho chi minh"
    assert second["experience_min"] is None
    assert second["errors"]
    assert all("salary_prediction" not in row for row in result["rows"])


@pytest.mark.parametrize(
    "content", [b"a,a\n1,2\n", b"\xff\xfe", b"x" * (5 * 1024 * 1024 + 1), b"a\n" + b"1\n" * 10001]
)
def test_invalid_or_oversized_uploads_are_rejected_without_silent_truncation(content):
    with pytest.raises(MarketError):
        MarketService().profile_columns(content)


def test_csv_page_has_explicit_limits_and_keeps_prediction_blocked():
    page = Path(__file__).parents[1] / "pages/tools/preview_csv.py"
    app = AppTest.from_file(str(page), default_timeout=20).run()
    assert not app.exception
    assert len(app.get("file_uploader")) == 1
    assert any("ML bị chặn" in item.value for item in app.info)
    assert len(app.get("download_button")) == 1
