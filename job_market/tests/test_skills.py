"""Small synthetic postings test logic only; never used as market data."""

import json
import os
import subprocess
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

from career_market import MarketService


def test_mobile_frameworks_observed_in_titles_are_included_as_technology_evidence():
    result = MarketService().extract_skills("Flutter Developer / Unity Developer")
    assert result["skills"] == ["Flutter", "Unity"]
    assert all(item["field"] == "title" for item in result["skill_evidence"])


def test_framework_database_and_cloud_aliases_keep_original_evidence():
    result = MarketService().extract_skills(
        "ReactJS / React.js / Vuejs / .NET / MySQL / PostgreSQL / AWS / Kubernetes"
    )
    assert set(result["skills"]) == {
        "React",
        "Vue.js",
        ".NET",
        "MySQL",
        "PostgreSQL",
        "AWS",
        "Kubernetes",
    }
    assert "C#" not in result["skills"]
    assert len([s for s in result["skills"] if s == "React"]) == 1
    assert all(e["field"] == "title" and "ReactJS" in e["text"] for e in result["skill_evidence"])


def test_languages_are_unique_but_keep_evidence_from_each_posting_field():
    result = MarketService().extract_skills(
        "JavaScript Developer", "Build Java services. Java services.", "JavaScript and Java"
    )
    assert result == {
        "skills": ["JavaScript", "Java"],
        "skill_evidence": [
            {"skill": "JavaScript", "field": "title", "text": "JavaScript Developer"},
            {"skill": "Java", "field": "description", "text": "Build Java services."},
            {"skill": "JavaScript", "field": "requirements", "text": "JavaScript and Java"},
            {"skill": "Java", "field": "requirements", "text": "JavaScript and Java"},
        ],
        "skills_reason": "Có bằng chứng kỹ năng công nghệ trong tin.",
    }


def test_c_family_boundaries_and_dotnet_do_not_infer_other_languages():
    service = MarketService()
    assert service.extract_skills("Objective-C / C++ / C# / C Developer")["skills"] == [
        "Objective-C",
        "C++",
        "C#",
        "C",
    ]
    assert service.extract_skills("Objective-C, C++, C# and .NET")["skills"] == [
        "Objective-C",
        "C++",
        "C#",
        ".NET",
    ]
    assert service.extract_skills(".NET developer")["skills"] == [".NET"]


def test_explicit_language_names_are_case_insensitive_and_not_substrings():
    result = MarketService().extract_skills(
        "TypeScript / PYTHON / php / Kotlin / Swift / Dart / Ruby",
        "javascript, pythonic, Javabeans, typescripted, HR, Scrum, React, AWS, MySQL",
    )
    assert result["skills"] == [
        "TypeScript",
        "Python",
        "PHP",
        "Kotlin",
        "Swift",
        "Dart",
        "Ruby",
        "JavaScript",
        "React",
        "AWS",
        "MySQL",
    ]


def test_go_alias_requires_technical_context_for_the_common_word():
    service = MarketService()
    assert service.extract_skills("Golang Developer", requirements="Develop services in Go")[
        "skills"
    ] == ["Go"]
    assert service.extract_skills("Go Developer")["skills"] == ["Go"]
    assert service.extract_skills("Backend", requirements="Kinh nghiệm lập trình Go")["skills"] == [
        "Go"
    ]
    assert (
        service.extract_skills(
            "Marketing Executive", "We go to market. Go home after work. Go-to-market strategy."
        )["skills"]
        == []
    )


def test_r_and_sql_are_languages_only_with_language_evidence():
    service = MarketService()
    result = service.extract_skills(
        "SQL Developer", "Use R programming for analysis.", "Kinh nghiệm lập trình SQL"
    )
    assert result["skills"] == ["SQL", "R"]
    assert result["skill_evidence"][1] == {
        "skill": "R",
        "field": "description",
        "text": "Use R programming for analysis.",
    }
    assert (
        service.extract_skills(
            "Marketing",
            "R&D team, HR support; r is a letter. Generate SQL (sales qualified leads).",
        )["skills"]
        == []
    )


def test_missing_jd_and_no_match_have_explicit_reasons_without_inferred_skills():
    service = MarketService()
    title_only = service.extract_skills("Python Developer")
    assert title_only["skills_reason"] == (
        "Có bằng chứng kỹ năng công nghệ trong tin. Thiếu JD/yêu cầu: chỉ xét tiêu đề."
    )
    assert {item["field"] for item in title_only["skill_evidence"]} == {"title"}
    assert service.extract_skills("Chuyên viên văn phòng", "Quản lý hồ sơ") == {
        "skills": [],
        "skill_evidence": [],
        "skills_reason": "Không tìm thấy bằng chứng kỹ năng trong danh mục đã xác minh.",
    }
    assert "Thiếu JD/yêu cầu" in service.extract_skills("")["skills_reason"]


def test_technical_lists_include_go_r_sql_but_do_not_borrow_context_from_other_sentences():
    service = MarketService()
    assert service.extract_skills("Backend", requirements="Python, Go, R, SQL")["skills"] == [
        "Python",
        "Go",
        "R",
        "SQL",
    ]
    assert service.extract_skills(
        "Python Developer",
        "We go to market. The letter r is on the form. Sales qualified SQL leads.",
    )["skills"] == ["Python"]
    assert (
        service.extract_skills("Bank operations", "Process SWIFT payments and PHP currency.")[
            "skills"
        ]
        == []
    )


def test_cli_extracts_the_same_field_specific_language_result():
    root = Path(__file__).parents[1]
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "career_market",
            "skills",
            "--title",
            "JavaScript Developer",
            "--description",
            "Build Java services.",
            "--requirements",
            "Use Python",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout) == MarketService().extract_skills(
        "JavaScript Developer", "Build Java services.", "Use Python"
    )


def test_later_technical_mention_is_not_hidden_by_an_earlier_common_word():
    result = MarketService().extract_skills(
        "Backend", "Go home after work; develop services in Go."
    )
    assert result["skills"] == ["Go"]
    assert result["skill_evidence"] == [
        {
            "skill": "Go",
            "field": "description",
            "text": "Go home after work; develop services in Go.",
        }
    ]


def test_swift_programming_evidence_survives_banking_domain_context():
    service = MarketService()
    assert service.extract_skills("iOS Developer (Swift, Banking)")["skills"] == ["Swift"]
    assert service.extract_skills(
        "Mobile Developer", requirements="Use Swift programming for bank payment apps."
    )["skills"] == ["Swift"]
    assert (
        service.extract_skills(
            "Bank operations", "Manage SWIFT bank-payment messaging and SWIFT transfers."
        )["skills"]
        == []
    )


def test_php_programming_evidence_survives_currency_domain_context():
    service = MarketService()
    assert service.extract_skills("PHP Developer for currency platform")["skills"] == ["PHP"]
    assert service.extract_skills(
        "Backend", requirements="Use PHP programming to display peso currency."
    )["skills"] == ["PHP"]
    assert service.extract_skills("Finance", "Salary 50000 PHP pesos per month.")["skills"] == []


def test_sql_query_language_is_not_lost_for_marketing_software():
    service = MarketService()
    assert service.extract_skills("SQL Developer for marketing analytics")["skills"] == ["SQL"]
    assert service.extract_skills("Data Analyst", "Write SQL queries and optimize joins.")[
        "skills"
    ] == ["SQL"]
    assert (
        service.extract_skills("Marketing", "Generate SQL leads for our sales team.")["skills"]
        == []
    )


def test_c_is_not_a_vietnamese_combining_letter_certificate_or_finance_acronym():
    service = MarketService()
    assert (
        service.extract_skills(
            "Operations", "Ca\u0301c công việc, Anh văn tương đương C, phát hành L/C."
        )["skills"]
        == []
    )
    result = service.extract_skills("Embedded", requirements="Use C to build firmware.")
    assert result["skills"] == ["C"]
    assert result["skill_evidence"] == [
        {"skill": "C", "field": "requirements", "text": "Use C to build firmware."}
    ]


def test_skills_page_filters_postings_and_keeps_evidence_in_the_csv():
    page = Path(__file__).parents[1] / "pages/tools/skills.py"
    app = AppTest.from_file(str(page), default_timeout=20).run()
    assert not app.exception
    assert "Ngôn ngữ lập trình" in app.title[0].value
    app.selectbox[0].select("jobs-2026").run()
    assert not app.exception
    assert any("Thiếu JD" in item.value for item in app.warning)
    app.multiselect[0].select("Java").run()
    assert not app.exception
    postings = app.dataframe[0].value
    assert len(postings) > 0
    assert all("Java" in json.loads(value) for value in postings["skills"])
    evidence = app.dataframe[1].value
    assert set(evidence["field"]) == {"title"}
    assert all("java" in text.lower() for text in evidence["text"])
    import csv
    import io

    rows = list(csv.DictReader(io.StringIO(app.code[0].value)))
    assert len(rows) == len(postings)
    assert json.loads(rows[0]["skill_evidence"])
    assert rows[0]["source_id"] == "jobs-2026"
    assert rows[0]["job_url"].startswith("https://")
    assert "Thiếu JD/yêu cầu" in rows[0]["skills_reason"]
