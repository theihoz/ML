"""Small synthetic salary strings test logic only; never market/training fixtures."""

from career_market import MarketService


def test_bounded_vnd_month_preserves_both_ends_and_target():
    assert MarketService().normalize_salary("20–30 triệu VND/tháng") == {
        "salary_lower": 20_000_000,
        "salary_upper": 30_000_000,
        "salary_midpoint": 25_000_000,
        "salary_currency": "VND",
        "salary_period": "MONTH",
        "salary_basis": "unknown",
        "salary_kind": "bounded",
        "salary_status": "valid",
        "salary_reason": "eligible_vnd_month",
        "salary_target_vnd_month": 25_000_000,
    }


def test_fixed_salary_accepts_decimal_comma_and_grouped_thousands():
    service = MarketService()
    for raw, expected in [
        ("20,5 triệu VND/tháng", 20_500_000),
        ("20.500.000 VND/tháng", 20_500_000),
        ("20,500,000 VND/month", 20_500_000),
        ("20.500,50 VND/tháng", 20_500.5),
        ("20,500.50 VND/month", 20_500.5),
        ("25000k VND/month", 25_000_000),
    ]:
        result = service.normalize_salary(raw)
        assert (
            result["salary_lower"],
            result["salary_upper"],
            result["salary_midpoint"],
            result["salary_target_vnd_month"],
            result["salary_kind"],
        ) == (expected, expected, expected, expected, "fixed")


def test_missing_units_keep_amounts_for_review_without_a_target():
    for raw, currency, period, reason in [
        ("20–30 triệu VND", "VND", None, "missing_period"),
        ("20–30 triệu/tháng", None, "MONTH", "missing_currency"),
        ("20–30 triệu", None, None, "missing_currency_and_period"),
    ]:
        result = MarketService().normalize_salary(raw)
        assert (
            result["salary_lower"],
            result["salary_upper"],
            result["salary_currency"],
            result["salary_period"],
            result["salary_status"],
            result["salary_reason"],
            result["salary_target_vnd_month"],
        ) == (20_000_000, 30_000_000, currency, period, "review", reason, None)


def test_foreign_or_yearly_salary_preserves_units_and_basis_without_conversion():
    for raw, lower, upper, currency, period, basis in [
        ("60,000–90,000 USD/year gross", 60_000, 90_000, "USD", "YEAR", "gross"),
        ("$1.500,50 - $2.000,50/month net", 1500.5, 2000.5, "USD", "MONTH", "net"),
        ("240–360 triệu VND/năm", 240_000_000, 360_000_000, "VND", "YEAR", "unknown"),
        ("20–30 triệu đồng mỗi tháng (gross)", 20_000_000, 30_000_000, "VND", "MONTH", "gross"),
    ]:
        result = MarketService().normalize_salary(raw)
        assert (
            result["salary_lower"],
            result["salary_upper"],
            result["salary_currency"],
            result["salary_period"],
            result["salary_basis"],
        ) == (lower, upper, currency, period, basis)
        if (currency, period) != ("VND", "MONTH"):
            assert (result["salary_target_vnd_month"], result["salary_reason"]) == (
                None,
                "non_vnd_month",
            )
        else:
            assert result["salary_target_vnd_month"] == 25_000_000


def test_single_bounds_and_negotiable_values_never_become_targets():
    for raw, kind, lower, upper, reason in [
        ("Thỏa thuận", "negotiable", None, None, "negotiable"),
        ("Lương: Cạnh tranh", "competitive", None, None, "competitive"),
        ("upto 30 triệu VND/tháng", "upper_bound", None, 30_000_000, "single_bound"),
        ("up to 30 triệu VND/tháng", "upper_bound", None, 30_000_000, "single_bound"),
        ("Tới 30 triệu VND/tháng", "upper_bound", None, 30_000_000, "single_bound"),
        ("Đến 30 triệu VND/tháng", "upper_bound", None, 30_000_000, "single_bound"),
        ("Trên 20 triệu VND/tháng", "lower_bound", 20_000_000, None, "single_bound"),
        ("Từ 20 triệu VND/tháng", "lower_bound", 20_000_000, None, "single_bound"),
    ]:
        result = MarketService().normalize_salary(raw)
        assert (
            result["salary_kind"],
            result["salary_lower"],
            result["salary_upper"],
            result["salary_midpoint"],
            result["salary_target_vnd_month"],
            result["salary_reason"],
        ) == (kind, lower, upper, None, None, reason)


def test_invalid_inverted_negative_and_conflicting_amounts_require_review():
    for raw, reason in [
        ("30–20 triệu VND/tháng", "inverted_range"),
        ("-20 triệu VND/tháng", "negative_amount"),
        ("20 - -30 triệu VND/tháng", "negative_amount"),
        ("0 VND/tháng", "invalid_amount"),
        ("20,5,0 triệu VND/tháng", "invalid_amount"),
        ("20..000 VND/tháng", "invalid_amount"),
        ("20–30 triệu VND USD/tháng", "conflicting_currency"),
        ("20–30 triệu VND/tháng/year", "conflicting_period"),
        ("20–30 triệu VND/tháng gross net", "conflicting_basis"),
        ("20–30 triệu VND/tháng + thưởng 10 triệu", "invalid_amount"),
        (None, "missing_salary"),
        ("", "missing_salary"),
    ]:
        result = MarketService().normalize_salary(raw)
        assert (
            result["salary_status"],
            result["salary_reason"],
            result["salary_target_vnd_month"],
        ) == ("review", reason, None)


def test_salary_prefixes_and_vietnamese_range_connectors_keep_correct_bounds():
    for raw, lower, upper, kind in [
        ("Lương: Dưới9 Tr VND", None, 9_000_000, "upper_bound"),
        ("Lương: Trên15 Tr VND", 15_000_000, None, "lower_bound"),
        ("Từ 20 đến 30 triệu VND/tháng", 20_000_000, 30_000_000, "bounded"),
        ("20 triệu - 30 triệu VND/tháng", 20_000_000, 30_000_000, "bounded"),
    ]:
        result = MarketService().normalize_salary(raw)
        assert (result["salary_lower"], result["salary_upper"], result["salary_kind"]) == (
            lower,
            upper,
            kind,
        )
        if kind == "bounded":
            assert result["salary_target_vnd_month"] == 25_000_000
        else:
            assert result["salary_target_vnd_month"] is None


def test_salary_report_parses_all_real_sources_using_only_the_salary_field():
    report = MarketService().salary_report()
    assert (report["row_count"], report["target_n"], report["source_counts"]) == (
        3606,
        0,
        {"jobs-2023": 2056, "jobs-2026": 1550},
    )
    first = report["rows"][0]
    assert (
        first["raw_salary"],
        first["salary_lower"],
        first["salary_upper"],
        first["salary_period"],
        first["salary_reason"],
        first["salary_target_vnd_month"],
    ) == (
        "Lương: 15 Tr - 25 Tr VND",
        15_000_000,
        25_000_000,
        None,
        "missing_period",
        None,
    )  # This real JD mentions tháng; it is not salary-field evidence.
    assert first["job_id"] == "35BB6CB4"
    assert sum(report["reason_counts"].values()) == 3606
    assert sum(report["status_counts"].values()) == 3606
    assert MarketService().salary_report("jobs-2026")["row_count"] == 1550


def test_vnd_symbols_are_currency_evidence_but_not_a_pay_period():
    for raw, period, target in [
        ("20–30 triệu đ/tháng", "MONTH", 25_000_000),
        ("20–30 triệu ₫/tháng", "MONTH", 25_000_000),
        ("20–30 triệu VNĐ", None, None),
    ]:
        result = MarketService().normalize_salary(raw)
        assert (
            result["salary_currency"],
            result["salary_period"],
            result["salary_target_vnd_month"],
        ) == ("VND", period, target)


def test_salary_csv_exports_keep_raw_identity_and_reconcile_status_and_review():
    import csv
    import io

    service = MarketService()
    exports = service.salary_exports(service.salary_report())
    assert set(exports) == {"raw.csv", "normalized.csv", "status.csv", "review.csv"}
    tables = {name: list(csv.DictReader(io.StringIO(content))) for name, content in exports.items()}
    assert len(tables["raw.csv"]) == len(tables["normalized.csv"]) == 3606
    assert len(tables["review.csv"]) == 3606
    assert sum(int(row["n"]) for row in tables["status.csv"]) == 3606
    assert sum(int(row["target_n"]) for row in tables["status.csv"]) == 0
    assert tables["raw.csv"][0]["raw_salary"] == "Lương: 15 Tr - 25 Tr VND"
    assert tables["normalized.csv"][0]["salary_target_vnd_month"] == ""
    assert tables["review.csv"][0]["job_id"] == "35BB6CB4"
    assert tables["normalized.csv"][2056]["source_id"] == "jobs-2026"


def test_midpoint_requires_explicit_currency_and_period_evidence():
    for raw in ["15–25 triệu", "15–25 triệu VND", "15–25 triệu/tháng"]:
        result = MarketService().normalize_salary(raw)
        assert (
            result["salary_lower"],
            result["salary_upper"],
            result["salary_midpoint"],
            result["salary_target_vnd_month"],
        ) == (15_000_000, 25_000_000, None, None)
    yearly = MarketService().normalize_salary("60–90 nghìn USD/year")
    assert (yearly["salary_midpoint"], yearly["salary_target_vnd_month"]) == (75_000, None)


def test_salary_page_smoke_shows_real_totals_review_and_four_csv_downloads():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    page = Path(__file__).parents[1] / "pages/tools/salary.py"
    app = AppTest.from_file(str(page), default_timeout=20).run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == ["3606", "0"]
    assert len(app.get("download_button")) == 4
    assert any("ML bị chặn" in item.value for item in app.info)
    assert app.dataframe[0].value.iloc[0]["salary_reason"] == "missing_period"
    app.selectbox[0].select("jobs-2026").run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == ["1550", "0"]
    app.text_input[0].input("20–30 triệu VND/tháng").run()
    assert not app.exception
    import json

    assert json.loads(app.json[-1].value)["salary_target_vnd_month"] == 25_000_000


def test_malformed_parentheses_cannot_turn_an_invalid_salary_into_a_target():
    for raw in ["(20 triệu VND/tháng", "20 triệu VND/tháng)", "(20 triệu VND/tháng)"]:
        result = MarketService().normalize_salary(raw)
        assert (
            result["salary_status"],
            result["salary_midpoint"],
            result["salary_target_vnd_month"],
        ) == ("review", None, None)
