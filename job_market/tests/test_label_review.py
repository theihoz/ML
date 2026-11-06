"""Mẫu duyệt nhãn và cách tính độ chính xác của bộ gán nhãn tự động (#79)."""

from pathlib import Path

import pandas as pd
import pytest

from career_market.label_review import REVIEW_COLUMNS, _skill_context, score_review

REVIEW = Path(__file__).parents[1] / "datasets/labels/2026-11-06/label_accuracy_review.csv"


def test_score_counts_only_reviewed_rows_and_skill_precision():
    review = pd.DataFrame(
        {
            "skills": ["Java|REST API", "Python", ""],
            "review_salary_ok": ["1", "0", "1"],
            "review_role_ok": ["1", "1", "1"],
            "review_level_ok": ["1", "", "0"],
            "review_experience_ok": ["", "", ""],
            "review_skills_wrong": ["REST API", "", ""],
        }
    )
    result = score_review(review)
    assert result["salary"] == {"reviewed": 3, "correct": 2, "accuracy_pct": pytest.approx(200 / 3)}
    assert result["level"]["reviewed"] == 2
    assert result["experience"]["accuracy_pct"] is None
    assert result["skills"]["assigned"] == 3
    assert result["skills"]["precision_pct"] == pytest.approx(200 / 3)
    assert result["skills"]["most_wrong"] == {"REST API": 1}


def test_skill_context_shows_the_text_around_each_match():
    context = _skill_context("Python|SQL", "Yêu cầu: thành thạo Python và SQL Server")
    assert "Python: …" in context and "SQL: …" in context


def test_saved_review_covers_every_field_and_reaches_the_reported_accuracy():
    review = pd.read_csv(REVIEW, dtype=str)
    assert len(review) >= 200
    assert set(REVIEW_COLUMNS) <= set(review.columns)
    result = score_review(review)
    assert result["salary"]["reviewed"] == len(review)
    assert result["role"]["accuracy_pct"] >= 95
    assert result["skills"]["precision_pct"] >= 98
