"""Visual outputs describe either model estimates or observed labels explicitly."""

from career_market import MarketService


def test_prediction_chart_has_three_actual_model_estimates_and_selected_city():
    result = MarketService().salary_scenarios("Data/ML", "HN")
    assert result["png"].startswith(b"\x89PNG")
    assert len(result["table"]) == 3
    hanoi = next(row for row in result["table"] if row["city"] == "HN")
    assert round(hanoi["salary_vnd_month"]) == 34456578
    assert hanoi["selected"] is True
    assert sum(row["selected"] for row in result["table"]) == 1


def test_salary_charts_use_evidenced_midpoints_and_distinct_postings():
    result = MarketService().salary_analysis("salary")
    assert result["posting_count"] == 14
    backend = next(row for row in result["roles"] if row["name"] == "Backend")
    assert backend["mean_vnd_month"] == 20250000
    assert backend["posting_count"] == 2
    assert all(
        result["charts"][key].startswith(b"\x89PNG") for key in ("roles", "regions", "skills")
    )
    assert result["experience"] == []
    assert result["charts"]["experience"] is None


def test_experience_chart_keeps_income_cohort_and_original_ranges_separate():
    result = MarketService().salary_analysis("income")
    assert result["posting_count"] == 2
    assert result["cohort"] == "advertised_monthly_income"
    assert sorted((r["experience_min"], r["experience_max"]) for r in result["experience"]) == [
        (1, 5),
        (2, 5),
    ]
    assert result["charts"]["experience"].startswith(b"\x89PNG")


def test_overview_uses_actual_counts_and_non_overlapping_location_groups():
    report = MarketService().market_overview()
    assert report["posting_count"] == 320
    assert report["salary_posting_count"] == 14
    assert report["model_count"] == 2
    assert sum(row["posting_count"] for row in report["regions"]) == 320
    assert round(report["mean_salary_vnd_month"]) == 45107143
    assert all(
        report["charts"][name].startswith(b"\x89PNG")
        for name in ("skills", "roles", "regions", "experience")
    )
