"""Synthetic upload fixtures exercise the public preview seam; never training data."""

import io

import pytest
from openpyxl import Workbook

from career_market import MarketError, MarketService


def workbook_bytes(sheets=None):
    workbook = Workbook()
    workbook.remove(workbook.active)
    for name, rows in (sheets or {"Profiles": [["role", "experience"], ["Backend", 2]]}).items():
        sheet = workbook.create_sheet(name)
        for row in rows:
            sheet.append(row)
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def test_lists_sheets_and_requires_explicit_selection_without_a_model(tmp_path):
    service = MarketService(raw_dir=tmp_path)
    content = workbook_bytes(
        {"Notes": [["note"], ["hello"]], "Profiles": [["role", "experience"], ["Backend", 2]]}
    )
    assert service.xlsx_sheets(content, filename="profiles.xlsx")["sheets"] == ["Notes", "Profiles"]
    with pytest.raises(MarketError, match="sheet"):
        service.xlsx_profile_columns(content, sheet=None)
    assert service.xlsx_profile_columns(content, sheet="Profiles")["columns"] == [
        "role",
        "experience",
    ]


def test_xlsx_uses_csv_normalization_and_preserves_raw_rows_mapping_and_errors(tmp_path):
    service = MarketService(raw_dir=tmp_path)
    content = workbook_bytes(
        {
            "Profiles": [
                ["nghe", "nam", "tech", "noilam"],
                ["Backend", 2, "ReactJS; Python", "ho chi minh"],
                [None, None, None, None],
                ["Không rõ", "bad", "Unknown", "HN"],
            ]
        }
    )
    mapping = {"role": "nghe", "experience": "nam", "skills": "tech", "location": "noilam"}
    result = service.preview_xlsx_profiles(content, mapping, sheet="Profiles")
    csv = service.preview_profiles(
        "nghe,nam,tech,noilam\nBackend,2,ReactJS; Python,ho chi minh\n,,,\nKhông rõ,bad,Unknown,HN\n".encode(),
        mapping,
    )
    assert result["row_count"] == 3
    assert result["valid_count"] == 1
    assert result["mapping"] == mapping
    assert [row["source_row"] for row in result["rows"]] == [2, 3, 4]
    for actual, expected in zip(result["rows"], csv["rows"]):
        for key in (
            "row_id",
            "role",
            "skills",
            "locations",
            "status",
            "errors",
            "warnings",
            "experience_min",
            "experience_max",
        ):
            assert actual[key] == expected[key]
    assert result["rows"][0]["raw"]["nam"] == 2
    assert result["rows"][1]["raw"]["nghe"] is None
    assert all("salary_prediction" not in row for row in result["rows"])
    assert b"source_row" in result["csv"]
    with pytest.raises(MarketError, match="ghép"):
        service.preview_xlsx_profiles(content, {}, sheet="Profiles")


@pytest.mark.parametrize(
    "content,filename",
    [
        (b"", "profiles.xlsx"),
        (b"not a workbook", "profiles.xlsx"),
        (workbook_bytes(), "profiles.xlsm"),
        (workbook_bytes(), "profiles.csv"),
        (b"x" * (5 * 1024 * 1024 + 1), "profiles.xlsx"),
    ],
)
def test_rejects_empty_malformed_non_xlsx_and_oversized_files(content, filename):
    with pytest.raises(MarketError):
        MarketService().xlsx_sheets(content, filename=filename)


def rewrite_zip(content, changes):
    from zipfile import ZIP_DEFLATED, ZipFile

    output = io.BytesIO()
    with ZipFile(io.BytesIO(content)) as source, ZipFile(output, "w", ZIP_DEFLATED) as target:
        for name in source.namelist():
            value = source.read(name)
            change = changes.get(name)
            target.writestr(name, change(value) if callable(change) else changes.get(name, value))
        for name, value in changes.items():
            if name not in source.namelist():
                target.writestr(name, value)
    return output.getvalue()


@pytest.mark.parametrize(
    "content",
    [
        workbook_bytes({"Profiles": [["role", "experience"], ["Backend", "=1+1"]]}),
        workbook_bytes({"Profiles": [["role", "experience"], ["Backend", 2]], "Other": [["=1+1"]]}),
        rewrite_zip(workbook_bytes(), {"xl/vbaProject.bin": b"macro"}),
        rewrite_zip(
            workbook_bytes(),
            {
                "[Content_Types].xml": lambda data: data.replace(
                    b"spreadsheetml.sheet.main+xml", b"ms-excel.sheet.macroEnabled.main+xml"
                )
            },
        ),
        rewrite_zip(
            workbook_bytes(),
            {
                "xl/worksheets/sheet1.xml": lambda data: (
                    b'<!DOCTYPE worksheet [<!ENTITY x "boom">]>' + data
                )
            },
        ),
        rewrite_zip(workbook_bytes(), {"xl/padding.xml": b"x" * (20 * 1024 * 1024 + 1)}),
    ],
)
def test_rejects_formula_macro_unsafe_xml_and_expanded_zip_before_any_preview(content):
    with pytest.raises(MarketError):
        MarketService().xlsx_sheets(content)


@pytest.mark.parametrize(
    "content,sheet",
    [
        (
            workbook_bytes({"Profiles": [["role", "experience"]] + [["Backend", 2]] * 10001}),
            "Profiles",
        ),
        (
            rewrite_zip(
                workbook_bytes(),
                {
                    "xl/worksheets/sheet1.xml": lambda data: (
                        data.replace(b'r="2"', b'r="10002"')
                        .replace(b"A2", b"A10002")
                        .replace(b"B2", b"B10002")
                    )
                },
            ),
            "Profiles",
        ),
        (workbook_bytes({"Profiles": [["role", "role"], ["Backend", 2]]}), "Profiles"),
        (workbook_bytes({"Profiles": [[None, "experience"], ["Backend", 2]]}), "Profiles"),
        (workbook_bytes({"Profiles": []}), "Profiles"),
        (workbook_bytes(), "Missing"),
        (workbook_bytes({"Profiles": [[str(i) for i in range(101)]]}), "Profiles"),
        (workbook_bytes({f"Sheet{i}": [["role", "experience"]] for i in range(21)}), "Sheet0"),
    ],
)
def test_rejects_invalid_sheet_structure_and_limits_without_truncation(content, sheet):
    with pytest.raises(MarketError):
        MarketService().xlsx_profile_columns(content, sheet=sheet)


def test_accepts_exact_row_limit_and_ignores_untrusted_small_dimensions():
    content = workbook_bytes({"Profiles": [["role", "experience"]] + [["Backend", 2]] * 10000})
    content = rewrite_zip(
        content,
        {"xl/worksheets/sheet1.xml": lambda data: data.replace(b'ref="A1:B10001"', b'ref="A1:B1"')},
    )
    assert MarketService().xlsx_profile_columns(content, sheet="Profiles")["row_count"] == 10000


def test_rejects_formula_text_and_unsupported_cell_types():
    from datetime import date

    for value in (" =SUM(1,2)", date(2026, 10, 30), True):
        content = workbook_bytes({"Profiles": [["role", "experience"], ["Backend", value]]})
        with pytest.raises(MarketError):
            MarketService().preview_xlsx_profiles(
                content, {"role": "role", "experience": "experience"}, sheet="Profiles"
            )


def test_xlsx_page_exposes_limits_and_no_model_requirement():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    page = Path(__file__).parents[1] / "pages/tools/preview_xlsx.py"
    app = AppTest.from_file(str(page), default_timeout=20).run()
    assert not app.exception
    assert len(app.get("file_uploader")) == 1
    assert any("20 MiB" in item.value and "10.000" in item.value for item in app.markdown)
    assert any("không cần model" in item.value for item in app.info)


def test_rejects_empty_workbook_without_worksheets():
    content = rewrite_zip(
        workbook_bytes(),
        {
            "xl/workbook.xml": lambda data: data.replace(
                data[data.index(b"<sheets>") : data.index(b"</sheets>") + 9], b"<sheets/>"
            )
        },
    )
    with pytest.raises(MarketError):
        MarketService().xlsx_sheets(content)


@pytest.mark.parametrize(
    "changes",
    [
        {"xl/worksheets/sheet1.xml": lambda data: data.replace(b'r="A2"', b'r="not-a-cell"')},
        {"xl/styles.xml": b"<styleSheet>"},
        {"xl/worksheets/sheet1.xml": lambda data: data.replace(b'r="2"', b'r="-2"')},
    ],
)
def test_malformed_package_structure_is_a_file_error(changes):
    content = rewrite_zip(workbook_bytes(), changes)
    with pytest.raises(MarketError):
        MarketService().xlsx_profile_columns(content, sheet="Profiles")
