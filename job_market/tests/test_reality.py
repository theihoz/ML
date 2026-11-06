"""Acceptance behavior at the agreed saved-model reality-check seam."""

from career_market.model.reality import reality_check


def test_reference_keeps_all_ten_national_role_cells():
    result = reality_check()
    reference = result["reference"]
    assert reference["total"] == 10
    assert {row["role"] for row in reference["cells"]} == {
        "Backend Developer",
        "Frontend Developer",
        "Fullstack Developer",
        "Mobile Developer",
        "DevOps / Cloud",
        "Kiểm thử (QA/QC)",
        "Data Engineer",
        "Data Analyst / BI",
        "AI / ML Engineer",
        "Business Analyst",
    }
    assert all(row["region"] == "" and row["level"] == "" for row in reference["cells"])
    assert reference["tolerance"] == 0.15
    assert reference["required_rate"] == 0.8
    assert reference["passed"] == (sum(row["passed"] for row in reference["cells"]) >= 8)


def test_missing_cohort_counts_against_the_denominator(tmp_path):
    import pandas as pd

    from career_market.data.reference import load_reference

    rows = load_reference()
    missing = rows[rows["purpose"] == "evaluation"].iloc[0].copy()
    missing["id"] = "missing-cohort"
    missing["role"] = "Role with no profiles"
    path = tmp_path / "reference.csv"
    pd.concat([rows, missing.to_frame().T], ignore_index=True).to_csv(path, index=False)
    reference = reality_check(reference_path=path)["reference"]
    assert reference["total"] == 11
    assert reference["scored"] == 10
    cell = reference["cells"][-1]
    assert cell["prediction"] is None
    assert cell["passed"] is False
    assert reference["pass_rate"] == sum(c["passed"] for c in reference["cells"]) / 11


def test_report_separates_source_statistics_and_verified_role_anchors():
    result = reality_check()
    assert len(result["calibration_cells"]) == 15
    assert all(c["statistic"] == "mean" and c["median"] == "" for c in result["calibration_cells"])
    assert result["unknown_basis_cells"]
    assert all(
        c["basis"] == "unknown" and c["year"] == "2025" for c in result["unknown_basis_cells"]
    )
    anchors = result["role_calibration_cells"]
    assert len(anchors) == 20
    assert {c["year"] for c in anchors} == {"2023", "2024"}
    assert all(c["basis"] == "gross" and c["sample_size"] == "" for c in anchors)
    assert {c["report_total_respondents"] for c in anchors} == {"2207", "2324"}
    assert all(
        c["printed_page"] and c["pdf_page"] and c["source_url"].startswith("https://itviec.com/")
        for c in anchors
    )
    assert len(result["context_cells"]) == 4
    assert {c["source_role"] for c in result["context_cells"]} == {
        "Cloud Engineer",
        "QA-QC",
        "QA - QC",
    }
    assert result["inference_year"] == 2026
